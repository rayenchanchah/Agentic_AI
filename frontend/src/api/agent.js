// Frontend code to communicate with the agent backend
export async function sendCommandToAgent(command) {
  const response = await fetch('/api/agent/command', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ command }),
  });
  
  return response.json();
}

export function subscribeToAgentUpdates(callback) {
  const socket = new WebSocket('ws://localhost:8080/agent/updates');
  
  socket.onmessage = (event) => {
    const update = JSON.parse(event.data);
    callback(update);
  };
  
  return () => socket.close();
}
