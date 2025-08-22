export default function Footer() {
  const buildId = import.meta.env.VITE_BUILD_ID || 'dev';
  const buildTimestamp = import.meta.env.VITE_BUILD_TIMESTAMP || new Date().toISOString();
  
  return (
    <footer style={{
      opacity: 0.6,
      fontSize: 12,
      padding: 8,
      borderTop: '1px solid #eee',
      marginTop: 'auto',
      textAlign: 'center'
    }}>
      Built by SOPHIA • BUILD_ID: {buildId} • {buildTimestamp}
      <br />
      <a href="/__build" style={{ color: '#666', textDecoration: 'none' }}>Build Info</a>
      {' | '}
      <a href="/healthz" style={{ color: '#666', textDecoration: 'none' }}>Health</a>
    </footer>
  );
}

