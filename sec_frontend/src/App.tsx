import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Home from './components/home';
import Login from './components/login';
import Register from './components/register';
import RequestPasswordReset from './components/request-password-reset';
import PasswordReset from './components/password-reset';
import Dashboard from './pages/Dashboard/Dashboard';
import Overview from './components/overview';
import './App.css'

function App() {
  return (
    <Router>
      <Routes>
        {/* Redirect root to Register */}
        <Route path="/" element={<Navigate to="/register" replace />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/request-password-reset" element={<RequestPasswordReset />} />
        <Route path="/password-reset" element={<PasswordReset />} />
        <Route path="/home" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/overview" element={<Overview selectedTicker="AAPL" />} />
        {/* Add any other routes you need */}
      </Routes>
    </Router>
  );
}

export default App;
