import { useEffect, useState } from 'react';

export default function useAvailability(apiUrl) {
  const [availability, setAvailability] = useState('checking');
  useEffect(() => {
    let disposed = false;
    let controller;
    let timeout;
    async function check() {
      setAvailability('checking');
      controller = new AbortController();
      timeout = window.setTimeout(() => controller.abort(), 20000);
      try {
        if (!apiUrl) throw new Error('Missing API URL');
        const url = new URL(apiUrl, window.location.origin);
        url.pathname = url.pathname.replace(/\/ask_mimi\/?$/, '').replace(/\/$/, '') + '/health';
        url.search = '';
        url.hash = '';
        const response = await fetch(url, { cache: 'no-store', signal: controller.signal });
        const data = await response.json();
        const ready = response.ok && data.status === 'ok' && data.api === 'ok' && data.database === 'ok';
        if (!disposed) setAvailability(ready ? 'available' : 'unavailable');
      } catch {
        if (!disposed) setAvailability('unavailable');
      } finally {
        window.clearTimeout(timeout);
      }
    }
    check();
    const interval = window.setInterval(check, 60000);
    return () => {
      disposed = true;
      window.clearInterval(interval);
      window.clearTimeout(timeout);
      controller?.abort();
    };
  }, [apiUrl]);
  return availability;
}
