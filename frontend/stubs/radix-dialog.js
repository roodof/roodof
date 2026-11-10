// Stand-in for @radix-ui/react-dialog, which cmdk imports only for Command.Dialog. Roodof renders
// Command inside its own native <dialog>, so the Radix dialog (and the scroll lock that injects a
// <style> element, refused by the app's CSP) is not bundled. Using Command.Dialog fails loudly.
function unavailable() { throw new Error('Command.Dialog is not bundled in Roodof; use Command inside a native dialog.'); }
export const Root = unavailable, Portal = unavailable, Overlay = unavailable, Content = unavailable;
