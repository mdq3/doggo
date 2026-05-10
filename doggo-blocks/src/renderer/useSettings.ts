import { useEffect, useState } from 'react';

export const useSettings = () => {
  const [hostname, setHostname] = useState('doggo.local');
  const [password, setPassword] = useState('doggo');

  useEffect(() => {
    void window.doggo.getSettings().then(({ hostname: h, password: p }) => {
      setHostname(h);
      setPassword(p);
    });
  }, []);

  const save = async () => {
    await window.doggo.saveSettings({ hostname, password });
  };

  return { hostname, setHostname, password, setPassword, save };
};
