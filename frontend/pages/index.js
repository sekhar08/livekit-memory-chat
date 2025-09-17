import { useState, useRef } from "react";
import { connect } from "livekit-client";

export default function Home() {
  const [url, setUrl] = useState("");
  const [tokenUrl, setTokenUrl] = useState("");
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const roomRef = useRef(null);
  const inputRef = useRef(null);

  const connectToRoom = async () => {
    if (!url) return alert('Enter LiveKit URL (ws:// or wss://).');
    try {
     
      let token = '';
      if (tokenUrl) {
        const resp = await fetch(tokenUrl + '?identity=web-user&room=default');
        const j = await resp.json();
        token = j.token;
      } else {
        token = prompt('Paste LiveKit token here (or provide token server URL above).');
      }
      const room = await connect(url, token);
      roomRef.current = room;
      setConnected(true);

      room.on('dataReceived', (payload, participant) => {
        try {
          const text = new TextDecoder().decode(payload);
          setMessages(m => [...m, { from: participant?.identity || participant?.sid || 'remote', text }]);
        } catch (e) {
          console.error(e);
        }
      });

      setMessages(m => [...m, { from: 'system', text: 'Connected to LiveKit room' }]);
    } catch (e) {
      alert('Failed to connect: ' + e.message);
      console.error(e);
    }
  };

  const sendMessage = async () => {
    const text = inputRef.current.value;
    if (!text || !roomRef.current) return;
    await roomRef.current.localParticipant.publishData(new TextEncoder().encode(text));
    setMessages(m => [...m, { from: 'me', text }]);
    inputRef.current.value = '';
  };

  return (
    <div style={{ padding: 20, fontFamily: 'Arial, sans-serif' }}>
      <h1>LiveKit Memory Chat</h1>
      <div style={{ marginBottom: 10 }}>
        <input placeholder="LIVEKIT URL (ws:// or wss://)" value={url} onChange={e=>setUrl(e.target.value)} style={{ width: 420 }} />
        <input placeholder="Token server URL (http://localhost:8000/token)" value={tokenUrl} onChange={e=>setTokenUrl(e.target.value)} style={{ width: 420, marginLeft: 8 }} />
        <button onClick={connectToRoom} style={{ marginLeft: 8 }}>Connect</button>
      </div>

      <div style={{ border: '1px solid #ddd', padding: 10, height: 320, overflow: 'auto' }}>
        {messages.map((m,i)=>(
          <div key={i} style={{ marginBottom: 8 }}>
            <strong>{m.from}:</strong> {m.text}
          </div>
        ))}
      </div>

      <div style={{ marginTop: 10 }}>
        <input ref={inputRef} placeholder="Type message..." style={{ width: 700 }} />
        <button onClick={sendMessage} style={{ marginLeft: 8 }}>Send</button>
      </div>
    </div>
  );
}