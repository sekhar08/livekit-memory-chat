import os
import asyncio
import logging
from dotenv import load_dotenv

# LiveKit client
from livekit import rtc

# mem0
from mem0 import MemoryClient

# Try importing google genai variations
try:
    # preferred package
    import google.genai as genai
except Exception:
    try:
        import google.generativeai as genai
    except Exception:
        genai = None

load_dotenv()

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('agent')

LIVEKIT_URL = os.getenv('LIVEKIT_URL', 'ws://localhost:7880')
LIVEKIT_KEY = os.getenv('LIVEKIT_API_KEY')
LIVEKIT_SECRET = os.getenv('LIVEKIT_API_SECRET')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')
MEM0_KEY = os.getenv('MEM0_API_KEY')

# mem0 client
memory = MemoryClient(api_key=MEM0_KEY)

# Initialize Gemini client depending on import
genai_client = None
if genai is not None:
    try:
        if hasattr(genai, 'configure'):
            genai.configure(api_key=GEMINI_KEY)
        # some versions use Client class
        if hasattr(genai, 'Client'):
            genai_client = genai.Client()
        else:
            genai_client = genai
        LOG.info('Gemini client initialized')
    except Exception as e:
        LOG.exception('Could not initialize Gemini client: %s', e)
else:
    LOG.warning('Gemini library not found. Install google-genai or google-generativeai.')

async def on_data_received(event: rtc.DataReceived):
    try:
        text = event.data.decode('utf-8')
    except Exception:
        LOG.exception('Failed to decode incoming data')
        return

    participant = event.participant
    user_id = getattr(participant, 'identity', None) or getattr(participant, 'sid', 'unknown')
    LOG.info('Received message from %s: %s', user_id, text)

    # 1) Search mem0 for relevant memories for this user
    mems = []
    try:
        mems = memory.search(text, filters={'AND': [{'user_id': user_id}]}) or []
    except Exception as e:
        LOG.warning('mem0 search failed: %s', e)

    context = ''
    if mems:
        try:
            # mems might be list of dicts with 'content'
            lines = []
            for m in mems:
                if isinstance(m, dict) and 'content' in m:
                    lines.append(m['content'])
                else:
                    lines.append(str(m))
            context = 'Memory:\n' + '\n'.join(lines) + '\n---\n'
        except Exception:
            context = ''

    # 2) Build prompt
    prompt = f"""You are a helpful assistant that personalizes replies using short memory.
{context}
User ({user_id}): {text}
Assistant:"""

    # 3) Call Gemini / GenAI
    reply = "Sorry, I could not produce a response."
    if genai_client is not None:
        try:
            # Try method patterns that different SDK versions expose
            if hasattr(genai_client, 'models') and hasattr(genai_client.models, 'generate_content'):
                # new-style interface
                resp = genai_client.models.generate_content(model='gemini-1.5', input=prompt)
                if hasattr(resp, 'candidates') and resp.candidates:
                    reply = resp.candidates[0].content or str(resp.candidates[0])
                elif hasattr(resp, 'output') and resp.output:
                    out0 = resp.output[0]
                    reply = getattr(out0, 'text', str(out0))
                else:
                    reply = str(resp)
            elif hasattr(genai_client, 'generate_text'):
                r2 = genai_client.generate_text(model='gemini-1.5', prompt=prompt)
                reply = getattr(r2, 'result', getattr(r2, 'text', str(r2)))
            else:
                r3 = genai.generate_text(prompt=prompt, model='gemini-1.5')
                reply = getattr(r3, 'result', getattr(r3, 'text', str(r3)))
        except Exception as e:
            LOG.exception('Gemini call failed: %s', e)
    else:
        LOG.error('No Gemini client available.')

    LOG.info('Replying to %s: %s', user_id, reply[:200])

    # 4) Save to mem0 (await if async)
    try:
        if asyncio.iscoroutinefunction(memory.add):
            await memory.add([{'role': 'user', 'content': text}, {'role': 'assistant', 'content': reply}], user_id=user_id)
        else:
            memory.add([{'role': 'user', 'content': text}, {'role': 'assistant', 'content': reply}], user_id=user_id)
    except Exception as e:
        LOG.warning('mem0 add failed: %s', e)

    # 5) Publish reply back to room
    try:
        await event.room.local_participant.publish_data(reply.encode('utf-8'))
    except Exception as e:
        LOG.exception('Failed to publish reply: %s', e)

async def main():
    LOG.info('Connecting to LiveKit at %s', LIVEKIT_URL)
    async with rtc.connect(LIVEKIT_URL, LIVEKIT_KEY, LIVEKIT_SECRET) as room:
        LOG.info('Connected to LiveKit, room: %s', getattr(room, 'name', 'unknown'))
        room.on(rtc.DataReceived, on_data_received)
        await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOG.info('Agent shutting down')
