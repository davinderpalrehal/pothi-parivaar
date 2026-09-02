/** Shell views that have drawer/tab/bottom-nav destinations. */
export const SHELL_VIEWS = ['catalog', 'tracker', 'shelves', 'honorifics', 'hermes']

export const ADD_BOOK_VIEW = 'add-book'

/** Add Book is not a nav destination; hide tab/bottom-nav selection while there. */
export function shellNavValue(currentView) {
  return currentView === ADD_BOOK_VIEW ? null : currentView
}

/** Save to Library returns to Catalog; Save & Add Next stays on Add Book. */
export function viewAfterAddBookPersist({ addNext }) {
  return addNext ? ADD_BOOK_VIEW : 'catalog'
}

export function viewAfterAddBookCancel() {
  return 'catalog'
}
