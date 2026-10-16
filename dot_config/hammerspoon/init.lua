-- macOS Omarchy bridge. OmniWM owns layouts; this file owns keyboard shortcuts.
require('hs.ipc')
-- Login items are an explicit user choice, not an effect of loading this file.
hs.window.animationDuration = 0
hs.hotkey.setLogLevel('warning')
local ok, result = pcall(require, 'omarchy')
if ok then
  omarchy = result
  voxtypeOSD = require('voxtype-osd').start()
  local previousShutdown=hs.shutdownCallback
  hs.shutdownCallback=function()
    voxtypeOSD.stop()
    if previousShutdown then previousShutdown() end
  end
else
  hs.alert.show('Omarchy shortcuts failed to load. Open Hammerspoon Console.')
  print(result)
end
