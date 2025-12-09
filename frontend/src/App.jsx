import React, {useEffect, useState} from 'react'


export default function App(){
const [items, setItems] = useState([])
useEffect(()=>{ fetch('/api/listings/').then(r=>r.json()).then(setItems) }, [])
return (
<div style={{padding:20}}>
<h1>Scraped Listings</h1>
<table>
<thead><tr><th>Title</th><th>URL</th><th>First seen</th></tr></thead>
<tbody>
{items.map(i => (
<tr key={i.id}><td>{i.title}</td><td><a href={i.url}>{i.url}</a></td><td>{i.first_seen}</td></tr>
))}
</tbody>
</table>
</div>
)
}