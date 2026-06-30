import { app, Tray, Menu, nativeImage, BrowserWindow } from 'electron'

let tray: Tray | null = null

// System tray with the same menu as the old Tauri app. Menu actions that the
// renderer must handle (new note, toggles, quit-flush) are sent over the 'tray'
// channel; show/hide is handled here in main.
export function createTray(win: BrowserWindow, iconPath: string): void {
  const image = nativeImage.createFromPath(iconPath)
  tray = new Tray(image.isEmpty() ? nativeImage.createEmpty() : image)
  tray.setToolTip('Antinote')

  const toggle = (): void => {
    if (win.isVisible()) {
      win.hide()
    } else {
      win.show()
      win.focus()
    }
  }

  const menu = Menu.buildFromTemplate([
    { label: 'Show/Hide', click: toggle },
    {
      label: 'New Note',
      click: () => {
        win.show()
        win.focus()
        win.webContents.send('tray', 'new-note')
      }
    },
    { type: 'separator' },
    {
      label: 'Toggle Always on Top',
      click: () => win.webContents.send('tray', 'toggle-aot')
    },
    {
      label: 'Toggle Auto-hide',
      click: () => win.webContents.send('tray', 'toggle-auto-hide')
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        // Let the renderer flush any pending save before we exit.
        win.webContents.send('tray', 'quit')
        setTimeout(() => app.quit(), 80)
      }
    }
  ])

  tray.setContextMenu(menu)

  app.on('will-quit', () => {
    tray?.destroy()
    tray = null
  })
}
