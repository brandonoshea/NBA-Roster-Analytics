import { Route, Routes } from 'react-router-dom'
import { Title } from './components/Title'
import { MainTable } from './components/Maintable'
import { PlayerProfile } from './components/PlayerProfile'

function App() {
  return (
    <>
      <Title />
      <Routes>
        <Route path="/" element={<MainTable />} />
        <Route path="/players/:playerId" element={<PlayerProfile />} />
      </Routes>
    </>
  )
}

export default App
