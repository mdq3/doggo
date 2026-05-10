import { useEffect, useState } from 'react';

export const useSettings = () => {
  const [hostname, setHostname] = useState('doggo.local');
  const [password, setPassword] = useState('doggo');

  useEffect(() => {
    window.doggo.getSettings().then(({ hostname, password }) => {
      setHostname(hostname);
      setPassword(password);
    });
  }, []);

  const save = async () => {
    await window.doggo.saveSettings({ hostname, password });
  };

  return { hostname, setHostname, password, setPassword, save };
};
