import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { Button } from './components/ui/button'
import DashboardPage from './pages/Dashboard/Dashboard'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div className='text-xl font-bold text-red-500'>
        <DashboardPage />
      </div>
    </>
  )
}

export default App
