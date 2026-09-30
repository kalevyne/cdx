import { Navigate, Route, Routes } from 'react-router'

import { RequireLogin } from '@/components/RequireLogin'
import { BrowsePage } from '@/pages/BrowsePage'
import { CommitDetailPage } from '@/pages/CommitDetailPage'
import { CommitPage } from '@/pages/CommitPage'
import { HistoryPage } from '@/pages/HistoryPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export function App() {
  return (
    <Routes>
      <Route element={<RequireLogin />}>
        <Route index element={<Navigate to="/browse" replace />} />
        <Route path="browse" element={<BrowsePage />} />
        <Route path="commit" element={<CommitPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="commits/:id" element={<CommitDetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
