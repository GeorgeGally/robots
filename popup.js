const STORAGE_KEY = 'robot-love-persistent-dismiss'
const COMMENTS_KEY = 'robot-love-comments'
const SESSION_STATS_KEY = 'robot-love-session-stats'

async function getCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
  return tab
}

function getOrigin(url) {
  try {
    return new URL(url).origin
  } catch {
    return null
  }
}

async function getPersistentDismissed() {
  try {
    const result = await chrome.storage.local.get(STORAGE_KEY)
    return result[STORAGE_KEY] || []
  } catch {
    return []
  }
}

async function setPersistentDismissed(origins) {
  await chrome.storage.local.set({ [STORAGE_KEY]: origins })
}

async function init() {
  const tab = await getCurrentTab()
  if (!tab) {
    document.getElementById('comments').textContent = 'Could not determine origin.'
    return
  }
  const origin = getOrigin(tab.url)
  if (!origin) {
    document.getElementById('comments').textContent = 'Could not determine origin.'
    return
  }

  const commentsEl = document.getElementById('comments')
  try {
    const result = await chrome.storage.local.get(`${COMMENTS_KEY}-${origin}`)
    const stored = result[`${COMMENTS_KEY}-${origin}`]
    if (stored) {
      commentsEl.textContent = stored
      commentsEl.classList.remove('empty')
    } else {
      commentsEl.textContent = 'No Robotlove post found on this site.'
    }
  } catch {
    commentsEl.textContent = 'Could not load post.'
  }

  try {
    const stats = await chrome.storage.local.get(SESSION_STATS_KEY)
    const sites = stats[SESSION_STATS_KEY] || []
    document.getElementById('stats').textContent =
      `Sites with posts: ${sites.length}`
  } catch {}

  const persistent = await getPersistentDismissed()
  const isDismissed = persistent.includes(origin)
  const btn = document.getElementById('dismissBtn')

  if (isDismissed) {
    btn.textContent = 'Unhide bar on this site'
    btn.classList.add('dismissed')
    btn.addEventListener('click', async () => {
      const updated = persistent.filter(o => o !== origin)
      await setPersistentDismissed(updated)
      btn.textContent = 'Permanently hide bar on this site'
      btn.classList.remove('dismissed')
    })
  } else {
    btn.addEventListener('click', async () => {
      if (persistent.includes(origin)) return
      persistent.push(origin)
      await setPersistentDismissed(persistent)
      btn.textContent = 'Unhide bar on this site'
      btn.classList.add('dismissed')
    })
  }
}

init()
