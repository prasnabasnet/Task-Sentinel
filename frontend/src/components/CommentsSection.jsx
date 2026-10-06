import { useEffect, useState, useCallback } from 'react'
import { commentsApi } from '../api'
import ApiHint from './ApiHint'
import { ErrorBanner } from './ui'
import { useAuth } from '../context/AuthContext'

export default function CommentsSection({ targetType, targetId }) {
  const { user } = useAuth()
  const [comments, setComments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [commentBody, setCommentBody] = useState('')
  const [replyTo, setReplyTo] = useState(null)

  const load = useCallback(async () => {
    if (!targetId) return
    setLoading(true)
    setError('')
    try {
      const data = await commentsApi.list({ target_type: targetType, target_id: targetId })
      setComments(Array.isArray(data) ? data : data.results || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [targetType, targetId])

  useEffect(() => {
    load()
  }, [load])

  const postComment = async (e) => {
    e.preventDefault()
    if (!commentBody.trim()) return
    setBusy(true)
    setError('')
    try {
      const body = replyTo
        ? { body: commentBody, parent: replyTo }
        : { body: commentBody, target_type: targetType, target_id: Number(targetId) }
      await commentsApi.create(body)
      setCommentBody('')
      setReplyTo(null)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const deleteComment = async (id) => {
    if (!confirm('Delete this comment?')) return
    try {
      await commentsApi.remove(id)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) {
    return <p className="muted">Loading comments…</p>
  }

  return (
    <div className="section" style={{ borderTop: '1px solid var(--border)', marginTop: '24px', paddingTop: '16px' }}>
      <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        Comments
        <ApiHint
          method="GET"
          path={`/api/comments/?target_type=${targetType}&target_id=${targetId}`}
        />
      </h3>

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      <div className="comment-list" style={{ display: 'flex', flexDirection: 'column', gap: '12px', margin: '12px 0' }}>
        {comments.length === 0 && <p className="muted">No comments yet.</p>}
        {comments.map((c) => (
          <div key={c.id} className="comment" style={{ background: '#f4f5f7', borderRadius: '3px', padding: '10px 12px' }}>
            <div className="comment-head" style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', marginBottom: '4px' }}>
              <strong>{c.author?.username || c.author?.email}</strong>
              <span className="muted small">
                {new Date(c.created_at).toLocaleString()}
              </span>
            </div>
            <p style={{ margin: '4px 0' }}>{c.body}</p>
            <div className="row" style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setReplyTo(c.id)}
              >
                Reply
              </button>
              {(user?.id === c.author?.id || ['SUPERADMIN', 'ORG_ADMIN', 'ADMIN'].includes(user?.role) || user?.is_superuser) && (
                <button
                  type="button"
                  className="btn btn-ghost btn-sm danger"
                  onClick={() => deleteComment(c.id)}
                >
                  Delete
                  <ApiHint method="DELETE" path={`/api/comments/${c.id}/`} />
                </button>
              )}
            </div>

            {c.replies?.map((r) => (
              <div key={r.id} className="comment reply" style={{ margin: '8px 0 0 16px', background: '#fff', border: '1px solid var(--border)', borderRadius: '3px', padding: '8px 10px' }}>
                <div className="comment-head" style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', marginBottom: '4px' }}>
                  <strong>{r.author?.username || r.author?.email}</strong>
                  <span className="muted small">
                    {new Date(r.created_at).toLocaleString()}
                  </span>
                </div>
                <p style={{ margin: '4px 0' }}>{r.body}</p>
                <div className="row" style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                  {(user?.id === r.author?.id || ['SUPERADMIN', 'ORG_ADMIN', 'ADMIN'].includes(user?.role) || user?.is_superuser) && (
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm danger"
                      onClick={() => deleteComment(r.id)}
                    >
                      Delete
                      <ApiHint method="DELETE" path={`/api/comments/${r.id}/`} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>

      <form onSubmit={postComment} className="stack comment-form" style={{ marginTop: '12px' }}>
        {replyTo && (
          <div className="row" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span className="muted small">Replying to comment #{replyTo}</span>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setReplyTo(null)}
            >
              Cancel reply
            </button>
          </div>
        )}
        <textarea
          rows={3}
          placeholder="Add a comment"
          value={commentBody}
          onChange={(e) => setCommentBody(e.target.value)}
          style={{ width: '100%', resize: 'vertical' }}
        />
        <div className="row end" style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
          <button type="submit" className="btn btn-primary btn-sm" disabled={busy}>
            Comment
            <ApiHint method="POST" path="/api/comments/" />
          </button>
        </div>
      </form>
    </div>
  )
}
