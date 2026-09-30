import { Navigate, Route, Routes } from 'react-router'

import { RequireLogin } from '@/components/RequireLogin'
import { BrowsePage } from '@/pages/BrowsePage'
import { CommitPage } from '@/pages/CommitPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export function App() {
  return (
    <Routes>
      <Route element={<RequireLogin />}>
        <Route index element={<Navigate to="/browse" replace />} />
        <Route path="browse" element={<BrowsePage />} />
        <Route path="commit" element={<CommitPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
