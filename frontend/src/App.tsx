import { Route, Routes } from 'react-router-dom'
import { Title } from './components/Title'
import { MainTable } from './components/Maintable'
import { PlayerProfile } from './components/PlayerProfile'
import { RosterBuilder } from './components/RosterBuilder'

function App() {
  return (
    <>
      <Title />
      <Routes>
        <Route path="/" element={<MainTable />} />
        <Route path="/players/:playerId" element={<PlayerProfile />} />
        <Route path="/rosters" element={<RosterBuilder />} />
      </Routes>
    </>
  )
}

export default App
