// Configuration - set to false to hide debug info in production
var DEBUG_MODE = true;

// Storage key for saving URL
var URL_STORAGE_KEY = "hotel_room_url";

// Volume control function
function setTVVolume(volume) {
  if (typeof webOS !== 'undefined' && webOS.service) {
    var request = webOS.service.request("luna://com.webos.service.audio", {
      method: "setVolume",
      parameters: {
        "volume": volume,
        "sessionType": "media"
      },
      onSuccess: function (inResponse) {
        console.log("Volume set successfully to:", volume);
        if (DEBUG_MODE) {
          var debugElement = document.getElementById("debug");
          if (debugElement) {
            debugElement.innerHTML += "<br>TV Volume set to: " + volume;
          }
        }
      },
      onFailure: function (inError) {
        console.error("Failed to set volume:", inError);
        if (DEBUG_MODE) {
          var debugElement = document.getElementById("debug");
          if (debugElement) {
            debugElement.innerHTML += "<br>Failed to set volume: " + JSON.stringify(inError);
          }
        }
      }
    });
  } else {
    console.log("WebOS service not available - running in browser/emulator");
    if (DEBUG_MODE) {
      var debugElement = document.getElementById("debug");
      if (debugElement) {
        debugElement.innerHTML += "<br>WebOS service not available (browser mode)";
      }
    }
  }
}

// Get current TV volume
function getTVVolume() {
  if (typeof webOS !== 'undefined' && webOS.service) {
    var request = webOS.service.request("luna://com.webos.service.audio", {
      method: "getVolume",
      parameters: {
        "sessionType": "media"
      },
      onSuccess: function (inResponse) {
        console.log("Current volume:", inResponse.volume);
        if (DEBUG_MODE) {
          var debugElement = document.getElementById("debug");
          if (debugElement) {
            debugElement.innerHTML += "<br>Current TV Volume: " + inResponse.volume;
          }
        }
      },
      onFailure: function (inError) {
        console.error("Failed to get volume:", inError);
      }
    });
  }
}

// Helper function to save URL to localStorage
function saveUrlToStorage(url) {
  if (typeof Storage !== "undefined" && url) {
    try {
      localStorage.setItem(URL_STORAGE_KEY, url);
      console.log("URL saved to localStorage:", url);
      return true;
    } catch (e) {
      console.error("Failed to save URL to localStorage:", e);
      return false;
    }
  }
  return false;
}

// Helper function to get saved URL from localStorage
function getSavedUrl() {
  if (typeof Storage !== "undefined") {
    try {
      var savedUrl = localStorage.getItem(URL_STORAGE_KEY);
      console.log("Retrieved URL from localStorage:", savedUrl);
      return savedUrl;
    } catch (e) {
      console.error("Failed to retrieve URL from localStorage:", e);
      return null;
    }
  }
  return null;
}

// Helper function to clear saved URL
function clearSavedUrl() {
  if (typeof Storage !== "undefined") {
    try {
      localStorage.removeItem(URL_STORAGE_KEY);
      console.log("Saved URL cleared from localStorage");
      return true;
    } catch (e) {
      console.error("Failed to clear URL from localStorage:", e);
      return false;
    }
  }
  return false;
}

// Helper function to extract URL from launch parameters
function extractUrlFromParams(inData) {
  if (!inData) {
    return null;
  }

  // Try different possible parameter structures
  if (inData.detail && inData.detail.url) {
    return inData.detail.url;
  }

  if (inData.url) {
    return inData.url;
  }

  // Try to access parameters at root level
  if (typeof inData === 'object') {
    for (var key in inData) {
      if (key === 'url') {
        return inData[key];
      }
    }
  }

  return null;
}

// Helper function to redirect to URL
function redirectToUrl(url, source) {
  var statusElement = document.getElementById("status");
  var debugElement = document.getElementById("debug");

  if (url) {
    var sourceText = source ? " (" + source + ")" : "";
    statusElement.innerHTML = "Loading room information..." + sourceText;

    if (DEBUG_MODE) {
      debugElement.innerHTML = "Redirecting to: " + url + " | Source: " + (source || "unknown");
    } else {
      debugElement.classList.add("hidden");
    }

    console.log("Redirecting to:", url, "from source:", source);

    // Add a small delay to show the loading message
    setTimeout(function () {
      window.location.href = url;
    }, 1500);
  } else {
    statusElement.innerHTML = "Ready - Waiting for room parameters";

    if (DEBUG_MODE) {
      debugElement.innerHTML = "No URL found";
    } else {
      debugElement.classList.add("hidden");
    }
  }
}

// Function to handle application startup (called when DOM is loaded)
function handleAppStartup() {
  var statusElement = document.getElementById("status");

  // Set TV volume to 10 when app starts
  console.log("Setting TV volume to 10...");
  getTVVolume(); // Get current volume first
  setTimeout(function () {
    setTVVolume(10); // Set volume to 10 after a small delay
  }, 500);

  // First, try to get saved URL from localStorage
  var savedUrl = getSavedUrl();

  if (savedUrl) {
    statusElement.innerHTML = "Found saved room URL - Loading...";
    redirectToUrl(savedUrl, "localStorage");
  } else {
    statusElement.innerHTML = "Ready - No saved room found";
    if (DEBUG_MODE) {
      var debugElement = document.getElementById("debug");
      debugElement.innerHTML = "No saved URL found in localStorage";
    }
  }
}

document.addEventListener(
  "webOSLaunch",
  function (inData) {
    var statusElement = document.getElementById("status");
    statusElement.innerHTML = "Application launched successfully";

    console.log("webOSLaunch event fired with data:", inData);

    // Set TV volume to 10 on launch
    console.log("Setting TV volume to 10 on launch...");
    setTimeout(function () {
      setTVVolume(10);
    }, 500);

    // Handle launch parameters
    var url = extractUrlFromParams(inData);

    if (url) {
      // Save new URL to localStorage for future use
      saveUrlToStorage(url);
      redirectToUrl(url, "launch parameters");
    } else {
      // No parameters provided, try to use saved URL
      handleAppStartup();
    }
  },
  true
);

document.addEventListener(
  "webOSRelaunch",
  function (inData) {
    var statusElement = document.getElementById("status");
    statusElement.innerHTML = "Application relaunched - Loading new content";

    console.log("webOSRelaunch event fired with data:", inData);

    // Set TV volume to 10 on relaunch
    console.log("Setting TV volume to 10 on relaunch...");
    setTimeout(function () {
      setTVVolume(10);
    }, 500);

    // Handle relaunch parameters
    var url = extractUrlFromParams(inData);

    if (url) {
      // Save new URL to localStorage for future use
      saveUrlToStorage(url);
      redirectToUrl(url, "relaunch parameters");
    } else {
      // No parameters provided, try to use saved URL
      handleAppStartup();
    }
  },
  true
);

// Handle DOM loaded event - for manual app launch from TV
document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM Content Loaded - Checking for saved URL");

  // Small delay to allow webOS events to fire first
  setTimeout(function () {
    // If we haven't redirected yet (no webOS launch events), check for saved URL
    var statusElement = document.getElementById("status");
    if (statusElement.innerHTML === "Initializing...") {
      handleAppStartup();
    }
  }, 1000);
});

// Also handle window load as backup
window.addEventListener("load", function () {
  console.log("Window Loaded - Checking for saved URL");

  // Small delay to allow webOS events to fire first
  setTimeout(function () {
    var statusElement = document.getElementById("status");
    if (statusElement.innerHTML === "Initializing...") {
      handleAppStartup();
    }
  }, 1500);
});

var hidden, visibilityChange;
if (typeof document.hidden !== "undefined") {
  hidden = "hidden";
  visibilityChange = "visibilitychange";
} else if (typeof document.webkitHidden !== "undefined") {
  hidden = "webkitHidden";
  visibilityChange = "webkitvisibilitychange";
}

document.addEventListener(
  visibilityChange,
  function () {
    var statusElement = document.getElementById("status");
    if (document[hidden]) {
      statusElement.innerHTML = "Application in background";
    } else {
      statusElement.innerHTML = "Application active";
    }
  },
  true
);