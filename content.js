(() => {
  if (window !== window.top) return

  const origin = window.location.origin
  if (origin.startsWith('chrome-extension://') || origin.startsWith('file://')) return

  const SESSION_DISMISSED = new Set()
  const STORAGE_KEY = 'robot-love-persistent-dismiss'
  const COMMENTS_KEY = 'robot-love-comments'
  const SESSION_STATS_KEY = 'robot-love-session-stats'
  const BAR_ID = 'robot-love-bar'
  const FETCH_TIMEOUT = 3000
  const MAX_BYTES = 10240
  const CYCLE_MS = 7000
  const TYPE_MS = 30

  async function getPersistentDismissed() {
    try {
      const result = await chrome.storage.local.get(STORAGE_KEY)
      return result[STORAGE_KEY] || []
    } catch {
      return []
    }
  }

  function createBar(paths, rawText) {
    const bar = document.createElement('div')
    bar.id = BAR_ID
    bar.style.cssText = `
      position: fixed; top: 0; left: 0; width: 100%; background: #1a1a1a;
      color: #e0e0e0; font-family: 'Courier New', Courier, monospace;
      font-size: 13px; box-sizing: border-box; z-index: 2147483647;
      line-height: 1.5; padding: 8px 80px 8px 12px;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      min-height: 32px; display: flex; align-items: center; gap: 8px;
      cursor: ${paths.length > 1 ? 'pointer' : 'default'};
    `

    bar.spacer = document.createElement('div')
    bar.spacer.id = BAR_ID + '-spacer'
    bar.spacer.style.cssText = `height: 40px;`

    const text = document.createElement('span')
    text.style.cssText = `overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;`

    let currentIndex = 0
    let timer = null

    function scheduleNext() {
      if (paths.length < 2) return
      timer = setTimeout(() => {
        currentIndex = (currentIndex + 1) % paths.length
        typePath(currentIndex)
      }, CYCLE_MS)
    }

    function typePath(index) {
      const target = `Disallow: ${paths[index]}`
      text.textContent = ''
      let i = 0
      function typeLoop() {
        if (i < target.length) {
          text.textContent += target[i]
          i++
          setTimeout(typeLoop, TYPE_MS)
        } else {
          scheduleNext()
        }
      }
      typeLoop()
    }

    typePath(0)

    bar.addEventListener('click', () => {
      if (paths.length < 2) return
      clearTimeout(timer)
      currentIndex = (currentIndex + 1) % paths.length
      typePath(currentIndex)
    })

    const link = document.createElement('a')
    link.textContent = '[raw]'
    link.style.cssText = `
      color: #666; text-decoration: none; flex-shrink: 0;
      font-size: 11px; cursor: pointer;
    `
    link.addEventListener('click', (e) => {
      e.stopPropagation()
      e.preventDefault()
      const blob = new Blob([rawText], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
    })
    link.addEventListener('mouseenter', () => { link.style.color = '#fff' })
    link.addEventListener('mouseleave', () => { link.style.color = '#666' })

    const close = document.createElement('button')
    close.innerHTML = '&times;'
    close.style.cssText = `
      position: absolute; right: 4px; top: 50%; transform: translateY(-50%);
      background: none; border: none; color: #666; font-size: 18px;
      cursor: pointer; width: 24px; height: 24px; display: flex;
      align-items: center; justify-content: center; padding: 0;
      line-height: 1;
    `
    close.addEventListener('mouseenter', () => { close.style.color = '#fff' })
    close.addEventListener('mouseleave', () => { close.style.color = '#666' })
    close.addEventListener('click', (e) => {
      e.stopPropagation()
      SESSION_DISMISSED.add(origin)
      clearTimeout(timer)
      if (bar._observer) bar._observer.disconnect()
      if (bar.spacer) bar.spacer.remove()
      bar.remove()
    })

    bar.appendChild(text)
    bar.appendChild(link)
    bar.appendChild(close)
    return bar
  }

  function injectBar(bar) {
    if (document.body) {
      document.body.insertBefore(bar.spacer, document.body.firstChild)
      document.body.insertBefore(bar, bar.spacer)
      return true
    }
    return false
  }

  async function fetchPost() {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT)

      const response = await fetch(`${origin}/robots.txt`, {
        signal: controller.signal,
        cache: 'no-cache',
      })
      clearTimeout(timeout)

      if (!response.ok) return null

      const text = (await response.text()).slice(0, MAX_BYTES)
      const lines = text.split('\n')

      let inBlock = false
      const paths = []

      for (const line of lines) {
        const stripped = line.trim()
        if (/^user-agent:\s*robots$/i.test(stripped)) {
          inBlock = true
          continue
        }
        if (!inBlock) continue
        if (/^user-agent:/i.test(stripped)) break
        if (stripped === '' && paths.length > 0) break
        if (/^disallow:/i.test(stripped)) {
          const path = stripped.slice('Disallow:'.length).trim()
          if (path) paths.push(path)
        }
      }

      if (paths.length === 0) return null

      return { paths, text }
    } catch {
      return null
    }
  }

  function isAttached(el) {
    return el && el.isConnected
  }

  function defendBar(bar) {
    const observer = new MutationObserver(() => {
      if (!isAttached(bar) && document.body) {
        if (SESSION_DISMISSED.has(origin)) { observer.disconnect(); return }
        document.body.insertBefore(bar.spacer, document.body.firstChild)
        document.body.insertBefore(bar, bar.spacer)
      }
    })
    observer.observe(document.body, { childList: true })
    bar._observer = observer
  }

  async function init() {
    const persistent = await getPersistentDismissed()
    if (persistent.includes(origin)) return

    const result = await fetchPost()
    if (!result) return

    const bar = createBar(result.paths, result.text)
    injectBar(bar)
    defendBar(bar)

    try {
      await chrome.storage.local.set({ [`${COMMENTS_KEY}-${origin}`]: `Disallow: ${result.paths.join('  ·  ')}` })
      const stats = await chrome.storage.local.get(SESSION_STATS_KEY)
      const sites = stats[SESSION_STATS_KEY] || []
      if (!sites.includes(origin)) {
        sites.push(origin)
        await chrome.storage.local.set({ [SESSION_STATS_KEY]: sites })
      }
    } catch {}
  }

  window.addEventListener('load', init)
})()
