import React, { useState, useEffect } from 'react';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { Generator } from './pages/Generator';
import { Dashboard } from './pages/Dashboard';
import { Admin } from './pages/Admin';
import { Login, Signup } from './pages/Auth';
import { User, UserRole } from './types';
import { MockBackend } from './services/mockBackend';

// Simple Router implementation for SPA without react-router-dom dependency 
// (keeps it single file compatible easier)

const App: React.FC = () => {
  const [page, setPage] = useState('home');
  const [user, setUser] = useState<User | null>(null);

  // Check for session (simulated)
  useEffect(() => {
    // In a real app, verify token here.
  }, []);

  const handleLogin = (u: User) => {
    setUser(u);
    setPage('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    setPage('home');
  };

  const navigate = (target: string) => {
    if ((target === 'generator' || target === 'dashboard') && !user) {
      setPage('login');
      return;
    }
    if (target === 'admin' && user?.role !== UserRole.ADMIN) {
      setPage('home');
      return;
    }
    setPage(target);
  };

  let content;
  switch (page) {
    case 'home':
      content = <Home onStart={() => navigate('generator')} />;
      break;
    case 'generator':
      content = user ? <Generator user={user} onUpdateUser={setUser} /> : <Login onLogin={handleLogin} onNavigate={navigate} />;
      break;
    case 'dashboard':
      content = user ? <Dashboard user={user} /> : <Login onLogin={handleLogin} onNavigate={navigate} />;
      break;
    case 'admin':
      content = user?.role === UserRole.ADMIN ? <Admin /> : <Home onStart={() => navigate('generator')} />;
      break;
    case 'login':
      content = <Login onLogin={handleLogin} onNavigate={navigate} />;
      break;
    case 'signup':
      content = <Signup onLogin={handleLogin} onNavigate={navigate} />;
      break;
    default:
      content = <Home onStart={() => navigate('generator')} />;
  }

  return (
    <Layout 
      user={user} 
      onLogout={handleLogout} 
      currentPage={page}
      onNavigate={navigate}
    >
      {content}
    </Layout>
  );
};

export default App;