import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './components/home';
import Dashboard from './pages/Dashboard/Dashboard';
import Overview from './components/overview';
import './App.css'
import { Button } from './components/ui/button'

function App() {
  return (
    <Router>
      <Routes>
        {/* Redirect root to Home */}
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/overview" element={<Overview ticker="AAPL" />} />
        {/* Add any other routes you need */}
      </Routes>
    </Router>
  );
}

export default App;
