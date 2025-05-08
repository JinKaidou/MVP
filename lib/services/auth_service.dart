// lib/services/auth_service.dart
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class AuthService extends ChangeNotifier {
  bool _isAuthenticated = false;
  String? _username;
  String? _userToken;
  String? _userId;

  // Base URL for your API server
  final String _baseUrl = 'http://10.0.2.2:5000/api'; // Android emulator
  // For physical devices, use your computer's actual IP address:
  // final String _baseUrl = 'http://192.168.1.X:5000/api';

  bool get isAuthenticated => _isAuthenticated;
  String? get username => _username;
  String? get userToken => _userToken;
  String? get userId => _userId;

  // Initialize auth state
  AuthService() {
    checkAuth();
  }

  // Check for existing authentication
  Future<bool> checkAuth() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final storedToken = prefs.getString('user_token');
      final storedUsername = prefs.getString('username');
      final storedUserId = prefs.getString('user_id');

      if (storedToken != null && storedUsername != null) {
        // Validate token with server
        final response = await http.post(
          Uri.parse('$_baseUrl/validate-token'),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $storedToken',
          },
        );

        if (response.statusCode == 200) {
          _userToken = storedToken;
          _username = storedUsername;
          _userId = storedUserId;
          _isAuthenticated = true;
          notifyListeners();
          return true;
        } else {
          // Token invalid, clean up
          await logout();
          return false;
        }
      }

      return false;
    } catch (e) {
      // If server is unavailable, assume offline mode with cached credentials
      final prefs = await SharedPreferences.getInstance();
      final storedToken = prefs.getString('user_token');
      final storedUsername = prefs.getString('username');

      if (storedToken != null && storedUsername != null) {
        _userToken = storedToken;
        _username = storedUsername;
        _isAuthenticated = true;
        notifyListeners();
        return true;
      }

      return false;
    }
  }

  // Login with username/password
  Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'username': username, 'password': password}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _userToken = data['token'];
        _username = username;
        _userId = data['user_id'];
        _isAuthenticated = true;

        // Save credentials
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('user_token', _userToken!);
        await prefs.setString('username', _username!);
        if (_userId != null) {
          await prefs.setString('user_id', _userId!);
        }

        notifyListeners();
        return {'success': true};
      } else if (response.statusCode == 401) {
        return {'success': false, 'message': 'Invalid credentials'};
      } else {
        return {'success': false, 'message': 'Server error, please try again'};
      }
    } catch (e) {
      // Handle offline login scenario - this is for development or when server is down
      if (username == 'admin' && password == 'password') {
        _userToken = 'offline_token';
        _username = username;
        _isAuthenticated = true;

        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('user_token', _userToken!);
        await prefs.setString('username', _username!);

        notifyListeners();
        return {'success': true, 'offline': true};
      }

      return {
        'success': false,
        'message': 'Connection error. Check your network or server status.',
        'error': e.toString(),
      };
    }
  }

  // Logout
  Future<void> logout() async {
    try {
      if (_userToken != null) {
        // Best effort to notify server
        await http
            .post(
              Uri.parse('$_baseUrl/logout'),
              headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer $_userToken',
              },
            )
            .timeout(
              const Duration(seconds: 5),
              onTimeout: () {
                return http.Response('', 408); // Timeout is ok for logout
              },
            );
      }
    } catch (e) {
      // Ignore errors on logout attempts
    } finally {
      // Always clean up local state regardless of server response
      _isAuthenticated = false;
      _username = null;
      _userToken = null;
      _userId = null;

      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('user_token');
      await prefs.remove('username');
      await prefs.remove('user_id');

      notifyListeners();
    }
  }

  // Get user profile info
  Future<Map<String, dynamic>> getUserProfile() async {
    if (!_isAuthenticated || _userToken == null) {
      return {'success': false, 'message': 'Not authenticated'};
    }

    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/user/profile'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_userToken',
        },
      );

      if (response.statusCode == 200) {
        return {'success': true, 'data': jsonDecode(response.body)};
      } else {
        return {'success': false, 'message': 'Failed to get profile'};
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'Connection error',
        'error': e.toString(),
      };
    }
  }

  // Check if connection with server is available
  Future<bool> checkServerConnection() async {
    try {
      final response = await http
          .get(Uri.parse('$_baseUrl/health'))
          .timeout(const Duration(seconds: 5));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
