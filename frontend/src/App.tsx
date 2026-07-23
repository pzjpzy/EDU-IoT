import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import GuidedWizard from './pages/GuidedWizard'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/sessions/:id" element={<GuidedWizard />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
