import React, { useEffect, useMemo, useState } from 'react'

function Stat({ label, value }) {
	return (
		<div className="stat">
			<div className="stat-label">{label}</div>
			<div className="stat-value">{value}</div>
		</div>
	)
}

function Badge({ children, tone = 'info' }) {
	return <span className={`badge badge-${tone}`}>{children}</span>
}

function Loader() {
	return (
		<div className="loader">
			<div className="dot"></div>
			<div className="dot"></div>
			<div className="dot"></div>
		</div>
	)
}

export default function App() {
	const [query, setQuery] = useState('coffee shops in seattle')
	const [limit, setLimit] = useState(10)
	const [type, setType] = useState('google_maps')
	const [submitting, setSubmitting] = useState(false)
	const [taskId, setTaskId] = useState(null)
	const [jobState, setJobState] = useState('idle') // idle | queued | refreshing
	const [listings, setListings] = useState([])
	const [sourceFilter, setSourceFilter] = useState('all')
	const [searchFilter, setSearchFilter] = useState('')
	const [refreshing, setRefreshing] = useState(false)
	const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
	const [sortKey, setSortKey] = useState('scraped_at')
	const [sortDir, setSortDir] = useState('desc')
	const [page, setPage] = useState(1)
	const pageSize = 10
	const [jobs, setJobs] = useState([])

	const filtered = useMemo(() => {
		return listings.filter(l => {
			const sourceOk = sourceFilter === 'all' ? true : l.source === sourceFilter
			const text = `${l.title ?? ''} ${l.url ?? ''} ${l.job_query ?? ''}`.toLowerCase()
			const searchOk = searchFilter.trim().length === 0 ? true : text.includes(searchFilter.toLowerCase())
			return sourceOk && searchOk
		})
	}, [listings, sourceFilter, searchFilter])

	const sorted = useMemo(() => {
		const arr = [...filtered]
		arr.sort((a, b) => {
			const va = a[sortKey]
			const vb = b[sortKey]
			let cmp = 0
			if (sortKey === 'scraped_at' || sortKey === 'first_seen') {
				const da = va ? new Date(va).getTime() : 0
				const db = vb ? new Date(vb).getTime() : 0
				cmp = da - db
			} else {
				const sa = (va || '').toString().toLowerCase()
				const sb = (vb || '').toString().toLowerCase()
				cmp = sa.localeCompare(sb)
			}
			return sortDir === 'asc' ? cmp : -cmp
		})
		return arr
	}, [filtered, sortKey, sortDir])

	const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
	const pageItems = useMemo(() => {
		const start = (page - 1) * pageSize
		return sorted.slice(start, start + pageSize)
	}, [sorted, page])

	async function submitJob(e) {
		e.preventDefault()
		setSubmitting(true)
		try {
			const res = await fetch('/api/run-job/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ job: { type, query, limit } })
			})
			const data = await res.json()
			setTaskId(data.task_id)
			setJobState('queued')
			// Auto refresh for ~45s (every 5s)
			let cycles = 0
			const interval = setInterval(async () => {
				cycles += 1
				setJobState('refreshing')
				await loadListings()
				setJobState('queued')
				if (cycles >= 9) {
					clearInterval(interval)
					setJobState('idle')
				}
			}, 5000)
		} catch (err) {
			console.error(err)
			alert('Failed to submit job')
		} finally {
			setSubmitting(false)
		}
	}

	async function loadListings() {
		setRefreshing(true)
		try {
			const res = await fetch('/api/listings/')
			const data = await res.json()
			setListings(Array.isArray(data) ? data : [])
			setPage(1)
		} catch (err) {
			console.error(err)
		} finally {
			setRefreshing(false)
		}
	}

	async function loadJobs() {
		try {
			const res = await fetch('/api/jobs/')
			const data = await res.json()
			setJobs(Array.isArray(data) ? data : [])
		} catch (err) {
			console.error(err)
		}
	}

	useEffect(() => {
		loadListings()
		loadJobs()
	}, [])

	useEffect(() => {
		localStorage.setItem('theme', theme)
		document.documentElement.dataset.theme = theme
	}, [theme])

	const total = listings.length
	const gmCount = listings.filter(l => l.source === 'google_maps').length
	const otherCount = total - gmCount

	return (
		<div className="app">
			<header className="header">
				<div className="brand">
					<div className="logo">⛏️</div>
					<div className="titles">
						<h1>Scraper Dashboard</h1>
						<p>Submit jobs, monitor progress, and review results</p>
					</div>
				</div>
				<div className="header-actions">
					<button className="btn" onClick={loadListings} disabled={refreshing}>
						{refreshing ? 'Refreshing…' : 'Refresh Results'}
					</button>
					<button className="btn" onClick={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))}>
						Theme: {theme}
					</button>
				</div>
			</header>

			<main className="content">
				<section className="panel">
					<div className="panel-header">
						<h2>Status</h2>
						{taskId ? <Badge tone="success">Task {taskId.slice(0, 8)}…</Badge> : <Badge>Idle</Badge>}
					</div>
					<div className="status-body">
						<div className="status-line">
							<span>Job State:</span>
							<span className={`status-pill pill-${jobState}`}>{jobState}</span>
						</div>
						<div className="status-actions">
							<button className="btn" onClick={loadListings} disabled={refreshing}>
								{refreshing ? 'Refreshing…' : 'Manual Refresh'}
							</button>
						</div>
					</div>
				</section>
				<section className="panel">
					<div className="panel-header">
						<h2>New Scrape Job</h2>
						{taskId ? <Badge tone="success">Last Task: {taskId.slice(0, 8)}…</Badge> : <Badge>Idle</Badge>}
					</div>
					<form className="grid" onSubmit={submitJob}>
						<div className="field">
							<label>Source</label>
							<select value={type} onChange={e => setType(e.target.value)}>
								<option value="google_maps">Google Maps</option>
								<option value="simple">Simple (CSS selectors)</option>
							</select>
						</div>
						<div className="field">
							<label>Query</label>
							<input value={query} onChange={e => setQuery(e.target.value)} placeholder="e.g., pizza near times square" />
						</div>
						<div className="field">
							<label>Limit</label>
							<input type="number" min={1} max={100} value={limit} onChange={e => setLimit(parseInt(e.target.value || '0', 10))} />
						</div>
						<div className="actions">
							<button className="btn btn-primary" type="submit" disabled={submitting}>
								{submitting ? <Loader /> : 'Enqueue Job'}
							</button>
						</div>
					</form>
				</section>

				<section className="panel">
					<div className="panel-header">
						<h2>Overview</h2>
					</div>
					<div className="stats">
						<Stat label="Total Listings" value={total} />
						<Stat label="Google Maps" value={gmCount} />
						<Stat label="Other Sources" value={otherCount} />
					</div>
				</section>

				<section className="panel">
					<div className="panel-header">
						<h2>Results</h2>
						<div className="panel-controls">
							<input className="input" placeholder="Search results…" value={searchFilter} onChange={e => setSearchFilter(e.target.value)} />
							<select className="input" value={sourceFilter} onChange={e => setSourceFilter(e.target.value)}>
								<option value="all">All Sources</option>
								<option value="google_maps">Google Maps</option>
							</select>
							<select className="input" value={sortKey} onChange={e => setSortKey(e.target.value)}>
								<option value="scraped_at">Sort by Scraped</option>
								<option value="first_seen">Sort by First Seen</option>
								<option value="title">Sort by Title</option>
								<option value="source">Sort by Source</option>
							</select>
							<select className="input" value={sortDir} onChange={e => setSortDir(e.target.value)}>
								<option value="desc">Desc</option>
								<option value="asc">Asc</option>
							</select>
							<button className="btn" onClick={() => exportCsv(sorted)}>Export CSV</button>
						</div>
					</div>
					<div className="table-wrap">
						<table className="table">
							<thead>
								<tr>
									<th>Title</th>
									<th>Source</th>
									<th>Query</th>
									<th>First Seen</th>
									<th>Scraped</th>
									<th>Link</th>
								</tr>
							</thead>
							<tbody>
								{pageItems.map((l, idx) => (
									<tr key={idx}>
										<td>{l.title || '—'}</td>
										<td>{l.source}</td>
										<td>{l.job_query || '—'}</td>
										<td>{l.first_seen ? new Date(l.first_seen).toLocaleString() : '—'}</td>
										<td>{l.scraped_at ? new Date(l.scraped_at).toLocaleString() : '—'}</td>
										<td>
											{l.url ? (
												<a className="link" href={l.url} target="_blank" rel="noreferrer">Open</a>
											) : '—'}
										</td>
									</tr>
								))}
							</tbody>
						</table>
						{sorted.length === 0 && (
							<div className="empty">
								<p>No results yet. Submit a job to get started.</p>
							</div>
						)}
						{sorted.length > 0 && (
							<div className="pagination">
								<button className="btn" disabled={page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}>Prev</button>
								<span className="page-indicator">Page {page} / {totalPages}</span>
								<button className="btn" disabled={page >= totalPages} onClick={() => setPage(p => Math.min(totalPages, p + 1))}>Next</button>
							</div>
						)}
					</div>
				</section>

				<section className="panel">
					<div className="panel-header">
						<h2>Job History</h2>
					</div>
					<div className="table-wrap">
						<table className="table">
							<thead>
								<tr>
									<th>Task</th>
									<th>Type</th>
									<th>Query</th>
									<th>Limit</th>
									<th>Status</th>
									<th>Created</th>
								</tr>
							</thead>
							<tbody>
								{jobs.slice(0, 10).map((j, idx) => (
									<tr key={idx}>
										<td>{j.task_id ? String(j.task_id).slice(0, 8) : '—'}</td>
										<td>{j.type || (j.job && j.job.type) || '—'}</td>
										<td>{j.query || (j.job && j.job.query) || '—'}</td>
										<td>{j.limit || (j.job && j.job.limit) || '—'}</td>
										<td>{j.status || 'pending'}</td>
										<td>{j.created_at ? new Date(j.created_at).toLocaleString() : '—'}</td>
									</tr>
								))}
							</tbody>
						</table>
						{jobs.length === 0 && (
							<div className="empty"><p>No jobs yet.</p></div>
						)}
					</div>
				</section>
			</main>

			<footer className="footer">
				<span>© {new Date().getFullYear()} Scraper Dashboard</span>
				<div className="footer-actions">
					<a className="link" href="/api/listings/" target="_blank" rel="noreferrer">Raw API</a>
				</div>
			</footer>
		</div>
	)
}

function exportCsv(rows) {
	// Create CSV from rows
	const headers = ['title','source','job_query','first_seen','scraped_at','url']
	const lines = [headers.join(',')]
	rows.forEach(r => {
		const vals = headers.map(h => {
			const v = r[h]
			const s = v == null ? '' : (typeof v === 'string' ? v : new Date(v).toISOString())
			const escaped = s.replace(/"/g, '""')
			return `"${escaped}"`
		})
		lines.push(vals.join(','))
	})
	const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
	const url = URL.createObjectURL(blob)
	const a = document.createElement('a')
	a.href = url
	a.download = `listings_${new Date().toISOString().slice(0,19)}.csv`
	document.body.appendChild(a)
	a.click()
	document.body.removeChild(a)
	URL.revokeObjectURL(url)
}