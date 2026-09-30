import { Route, Routes } from 'react-router'

import { RequireLogin } from '@/components/RequireLogin'
import { BrowsePage } from '@/pages/BrowsePage'
import { CommitDetailPage } from '@/pages/CommitDetailPage'
import { CommitPage } from '@/pages/CommitPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { HistoryPage } from '@/pages/HistoryPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { SponsorPage } from '@/pages/SponsorPage'

export function App() {
  return (
    <Routes>
      {/* Public: no login needed. */}
      <Route path="sponsor" element={<SponsorPage />} />

      <Route element={<RequireLogin />}>
        <Route index element={<DashboardPage />} />
        <Route path="browse" element={<BrowsePage />} />
        <Route path="commit" element={<CommitPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="commits/:id" element={<CommitDetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
