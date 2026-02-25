import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';
import '../models/user.dart';
import '../utils/constants.dart';

/// Result of token validation
enum TokenValidationResult { valid, invalid, networkError }

class AuthService {
  static const String _tokenKey = 'auth_token';
  static const String _userKey = 'user_data';
  static const String _userIdKey = 'user_id';
  static const String _userNameKey = 'user_name';
  
  static SharedPreferences? _prefs;
  static bool _isInitialized = false;
  static bool _isAuthChecked = false; // Track if auth check is complete
  static User? _currentUser;

  static Future<SharedPreferences> getPrefs() async {
    if (_prefs == null || !_isInitialized) {
      _prefs = await SharedPreferences.getInstance();
      _isInitialized = true;
    }
    return _prefs!;
  }

  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
    _isInitialized = true;
  }

  /// Check if auth initialization check is complete
  static bool isAuthChecked() {
    return _isAuthChecked;
  }

  /// Wait for auth check to complete and trigger it if not started
  static Future<bool> waitForAuthCheck() async {
    // If auth is already checked, return immediately
    if (_isAuthChecked) {
      return true;
    }
    
    // Initialize SharedPreferences if needed first
    await init();
    
    // Now trigger the auth check
    return await isLoggedIn();
  }
  
  static Future<bool> isLoggedIn() async {
    // First check if token exists locally
    final prefs = await getPrefs();
    final token = prefs.getString(_tokenKey);
    
    if (token == null || token.isEmpty) {
      _isAuthChecked = true;
      return false;
    }
    
    // First, do a quick local check - decode token to check expiration
    try {
      final localPayload = _decodeTokenLocally(token);
      if (localPayload == null) {
        // Token is invalid or expired locally, clear and return false
        await _clearLocalAuth();
        _isAuthChecked = true;
        return false;
      }
    } catch (e) {
      // Can't decode locally, try server validation
    }
    
    // Try to validate token with backend (with retries for cold start)
    final validationResult = await _validateTokenWithRetry();
    
    if (validationResult == TokenValidationResult.valid) {
      // Token is valid, update user info from server response
      _isAuthChecked = true;
      return true;
    } else if (validationResult == TokenValidationResult.invalid) {
      // Token is invalid/expired, clear local storage
      await _clearLocalAuth();
      _isAuthChecked = true;
      return false;
    } else {
      // Network error - we have a locally stored token that hasn't expired
      // Check if it's not expired locally before allowing access
      final localPayload = _decodeTokenLocally(token);
      if (localPayload != null) {
        // Token exists and hasn't expired locally, allow access
        // The API calls will fail if token is truly invalid
        _isAuthChecked = true;
        return true;
      } else {
        // Local token is expired, require fresh login
        await _clearLocalAuth();
        _isAuthChecked = true;
        return false;
      }
    }
  }

  /// Decode token locally to check expiration without server call
  static Map<String, dynamic>? _decodeTokenLocally(String token) {
    try {
      // Simple base64 decode and JSON parse to check exp claim
      final parts = token.split('.');
      if (parts.length != 3) return null;
      
      // Add padding if needed
      var payload = parts[1];
      final padLength = (4 - payload.length % 4) % 4;
      payload += '=' * padLength;
      
      final decoded = Uri.parse('data:application/json;base64,$payload').data?.contentAsBytes();
      if (decoded == null) return null;
      
      final String jsonStr = String.fromCharCodes(decoded);
      final Map<String, dynamic> payloadJson = Map<String, dynamic>.from(
        const JsonDecoder().convert(jsonStr)
      );
      
      // Check expiration
      final exp = payloadJson['exp'] as int?;
      if (exp != null) {
        final expirationDate = DateTime.fromMillisecondsSinceEpoch(exp * 1000);
        if (DateTime.now().isAfter(expirationDate)) {
          return null; // Token is expired
        }
      }
      
      return payloadJson;
    } catch (e) {
      return null;
    }
  }

  /// Validate token with backend with retry logic for cold start
  static Future<TokenValidationResult> _validateTokenWithRetry() async {
    const int maxRetries = 3;
    const int initialDelayMs = 1000;
    
    for (int attempt = 0; attempt < maxRetries; attempt++) {
      try {
        final headers = await _getHeadersForValidation();
        
        final response = await http.post(
          Uri.parse('${Constants.baseUrl}/api/auth/validate'),
          headers: headers,
        ).timeout(const Duration(seconds: 15));
        
        // Check for non-JSON responses
        if (response.body.isEmpty || 
            response.body.trim().startsWith('<') || 
            response.body.trim().startsWith('<!DOCTYPE')) {
          if (attempt < maxRetries - 1) {
            await Future.delayed(Duration(milliseconds: initialDelayMs * (attempt + 1)));
            continue;
          }
          return TokenValidationResult.networkError;
        }
        
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        
        if (response.statusCode >= 200 && response.statusCode < 300) {
          if (data['valid'] == true) {
            // Token is valid, update user info from server response
            final userId = data['user_id']?.toString(); // Convert int to String
            final userName = data['name'] as String?;
            final prefs = await getPrefs();
            
            if (userId != null) {
              await prefs.setString(_userIdKey, userId);
            }
            if (userName != null) {
              await prefs.setString(_userNameKey, userName);
            }
            
            // Also update stored user data if needed
            final currentUser = await getCurrentUser();
            if (currentUser != null) {
              final updatedUser = User(
                id: userId ?? currentUser.id,
                email: currentUser.email,
                name: userName ?? currentUser.name,
                createdAt: currentUser.createdAt,
              );
              _currentUser = updatedUser;
              await prefs.setString(_userKey, jsonEncode(updatedUser.toJson()));
            }
            
            return TokenValidationResult.valid;
          } else {
            return TokenValidationResult.invalid;
          }
        } else {
          return TokenValidationResult.invalid;
        }
      } catch (e) {
        if (attempt < maxRetries - 1) {
          await Future.delayed(Duration(milliseconds: initialDelayMs * (attempt + 1)));
          continue;
        }
        return TokenValidationResult.networkError;
      }
    }
    return TokenValidationResult.networkError;
  }

  /// Get headers for token validation (separate to avoid side effects)
  static Future<Map<String, String>> _getHeadersForValidation() async {
    final prefs = await getPrefs();
    final token = prefs.getString(_tokenKey);
    
    if (token == null || token.isEmpty) {
      return {'Content-Type': 'application/json'};
    }
    
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  /// Clear all local auth data
  static Future<void> _clearLocalAuth() async {
    final prefs = await getPrefs();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userKey);
    await prefs.remove(_userIdKey);
    await prefs.remove(_userNameKey);
    _currentUser = null;
  }

  static Future<String?> getToken() async {
    final prefs = await getPrefs();
    return prefs.getString(_tokenKey);
  }

  static Future<String?> getUserId() async {
    final prefs = await getPrefs();
    return prefs.getString(_userIdKey);
  }

  static String? getCurrentUserId() {
    return _prefs?.getString(_userIdKey);
  }

  static String? getCurrentUserName() {
    return _prefs?.getString(_userNameKey);
  }

  static Future<User?> getCurrentUser() async {
    if (_currentUser != null) return _currentUser;
    final prefs = await getPrefs();
    final userData = prefs.getString(_userKey);
    if (userData != null) {
      try {
        final Map<String, dynamic> json = jsonDecode(userData);
        _currentUser = User.fromJson(json);
        return _currentUser;
      } catch (e) {
        return null;
      }
    }
    return null;
  }

  static Future<User> signup(String name, String email, String password) async {
    try {
      final response = await ApiService.signup(name, email, password);
      final token = response['token'] as String;
      final userId = response['user_id'].toString(); // Convert int to String
      final userName = response['name'] as String?;
      
      final prefs = await getPrefs();
      await prefs.setString(_tokenKey, token);
      await prefs.setString(_userIdKey, userId);
      if (userName != null) {
        await prefs.setString(_userNameKey, userName);
      }
      
      _currentUser = User(
        id: userId,
        email: email,
        name: userName ?? name,
        createdAt: DateTime.now(),
      );
      await prefs.setString(_userKey, jsonEncode(_currentUser!.toJson()));
      _isAuthChecked = true; // Mark auth as checked after successful signup
      return _currentUser!;
    } catch (e) {
      rethrow;
    }
  }

  static Future<User> login(String email, String password) async {
    try {
      final response = await ApiService.login(email, password);
      final token = response['token'] as String;
      final userId = response['user_id'].toString(); // Convert int to String
      final userName = response['name'] as String?;
      
      final prefs = await getPrefs();
      await prefs.setString(_tokenKey, token);
      await prefs.setString(_userIdKey, userId);
      if (userName != null) {
        await prefs.setString(_userNameKey, userName);
      }
      
      _currentUser = User(
        id: userId,
        email: email,
        name: userName,
        createdAt: DateTime.now(),
      );
      await prefs.setString(_userKey, jsonEncode(_currentUser!.toJson()));
      _isAuthChecked = true; // Mark auth as checked after successful login
      return _currentUser!;
    } catch (e) {
      rethrow;
    }
  }

  static Future<void> logout() async {
    final prefs = await getPrefs();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userKey);
    await prefs.remove(_userIdKey);
    await prefs.remove(_userNameKey);
    _currentUser = null;
    _isAuthChecked = false; // Reset auth check flag for next login
  }
}

