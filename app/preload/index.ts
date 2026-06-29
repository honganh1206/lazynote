import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'
import type { Note } from '../main/db'

export type TrayAction = 'new-note' | 'toggle-aot' | 'toggle-auto-hide' | 'quit'

// Custom APIs for renderer
const api = {
  notes: {
    list: (): Promise<Note[]> => ipcRenderer.invoke('notes:list'),
    create: (content?: string): Promise<Note> => ipcRenderer.invoke('notes:create', content),
    update: (id: number, content: string): Promise<void> =>
      ipcRenderer.invoke('notes:update', id, content),
    delete: (id: number): Promise<void> => ipcRenderer.invoke('notes:delete', id)
  },
  settings: {
    get: (key: string): Promise<string | null> => ipcRenderer.invoke('settings:get', key),
    set: (key: string, value: string): Promise<void> => ipcRenderer.invoke('settings:set', key, value)
  },
  shell: {
    openExternal: (url: string): Promise<void> => ipcRenderer.invoke('shell:openExternal', url)
  },
  window: {
    setAlwaysOnTop: (b: boolean): Promise<void> => ipcRenderer.invoke('win:setAlwaysOnTop', b),
    hide: (): Promise<void> => ipcRenderer.invoke('win:hide'),
    show: (): Promise<void> => ipcRenderer.invoke('win:show')
  },
  onTray: (cb: (action: TrayAction) => void): (() => void) => {
    const handler = (_e: unknown, action: TrayAction): void => cb(action)
    ipcRenderer.on('tray', handler)
    return () => ipcRenderer.removeListener('tray', handler)
  }
}

export type Api = typeof api

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.api = api
}
