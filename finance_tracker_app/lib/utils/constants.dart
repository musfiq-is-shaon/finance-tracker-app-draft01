
class Constants {
  static const String appName = 'Finance Tracker';
  
  // ============================================================
  // CONFIGURATION: Choose your connection method
  // ============================================================
  // Options: 
  //   'emulator' - Android emulator (uses 10.0.2.2)
  //   'usb'      - USB debugging (uses localhost - requires adb reverse)
  //   'physical' - Physical device via WiFi (requires local IP)
  static const String connectionMode = 'physical';  // <-- CHANGE THIS: 'emulator', 'usb', or 'physical'
  
  // For 'physical' mode only: your computer's local IP address
  // Get it by running: ipconfig getifaddr en0 (on macOS)
  // Or check: System Settings > Network > IP Address
  static const String physicalDeviceIp = '192.168.68.117';  // <-- CHANGE THIS if using 'physical' mode
  
  // Port where your backend is running
  static const int backendPort = 5001;
  
  // Base URL for the backend API
  // - 'emulator': 10.0.2.2 (Android emulator connects to host localhost)
  // - 'usb': 127.0.0.1 (localhost - works with adb reverse)
  // - 'physical': your local IP (for WiFi debugging)
  static String get baseUrl {
    switch (connectionMode) {
      case 'usb':
        // For USB debugging: use localhost with adb reverse
        // Run: adb reverse tcp:5001 tcp:5001
        return 'http://127.0.0.1:$backendPort';
      case 'physical':
        // For physical device via WiFi
        return 'http://$physicalDeviceIp:$backendPort';
      case 'emulator':
      default:
        // For Android emulator
        return 'http://10.0.2.2:$backendPort';
    }
  }
  
  static const List<String> incomeCategories = [
    'Salary',
    'Business',
    'Investment',
    'Gift',
    'Other',
  ];
  
  static const List<String> expenseCategories = [
    'Food',
    'Transport',
    'Shopping',
    'Entertainment',
    'Bills',
    'Health',
    'Education',
    'Other',
  ];
}

