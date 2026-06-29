import { ipcMain, shell, BrowserWindow } from 'electron'
import { getNotes, getSettings } from './store'

export function registerIpc(): void {
  ipcMain.handle('notes:list', () => getNotes().list())
  ipcMain.handle('notes:create', (_e, content?: string) => getNotes().create(content ?? ''))
  ipcMain.handle('notes:update', (_e, id: number, content: string) => getNotes().update(id, content))
  ipcMain.handle('notes:delete', (_e, id: number) => getNotes().delete(id))

  ipcMain.handle('settings:get', (_e, key: string) => getSettings().get(key))
  ipcMain.handle('settings:set', (_e, key: string, value: string) => getSettings().set(key, value))

  ipcMain.handle('shell:openExternal', (_e, url: string) => shell.openExternal(url))

  ipcMain.handle('win:setAlwaysOnTop', (e, b: boolean) => {
    BrowserWindow.fromWebContents(e.sender)?.setAlwaysOnTop(b)
  })
  ipcMain.handle('win:hide', (e) => {
    BrowserWindow.fromWebContents(e.sender)?.hide()
  })
  ipcMain.handle('win:show', (e) => {
    const w = BrowserWindow.fromWebContents(e.sender)
    w?.show()
    w?.focus()
  })
}
