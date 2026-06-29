// Single import point for the preload bridge. Keeps window.api access in one file.
export type { Note } from '../../../main/db'
export const api = window.api
