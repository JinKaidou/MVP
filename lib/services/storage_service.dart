// lib/services/storage_service.dart
import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;

class StorageService {
  final String _baseUrl = 'http://10.0.2.2:5000/api';

  // Local storage keys
  static const String _chatHistoryKey = 'chat_history';
  static const String _appSettingsKey = 'app_settings';
  static const String _schoolMapCacheKey = 'school_map_cache';

  // Get auth token for API calls
  Future<String?> _getAuthToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('user_token');
  }

  // CHAT HISTORY FUNCTIONS

  // Save chat messages both locally and sync with server
  Future<bool> saveChatHistory(List<Map<String, dynamic>> messages) async {
    try {
      // Save locally first (for offline access)
      final prefs = await SharedPreferences.getInstance();
      final jsonData = jsonEncode(messages);
      await prefs.setString(_chatHistoryKey, jsonData);

      // Sync with server if possible
      final token = await _getAuthToken();
      if (token != null) {
        try {
          final response = await http
              .post(
                Uri.parse('$_baseUrl/chats/sync'),
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': 'Bearer $token',
                },
                body: jsonData,
              )
              .timeout(const Duration(seconds: 5));

          return response.statusCode == 200;
        } catch (e) {
          // If server sync fails, local save is still successful
          return true;
        }
      }

      return true;
    } catch (e) {
      return false;
    }
  }

  // Get chat history (prioritize server if available, fall back to local)
  Future<List<Map<String, dynamic>>> getChatHistory() async {
    try {
      final token = await _getAuthToken();
      if (token != null) {
        try {
          final response = await http
              .get(
                Uri.parse('$_baseUrl/chats/history'),
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': 'Bearer $token',
                },
              )
              .timeout(const Duration(seconds: 5));

          if (response.statusCode == 200) {
            final List<dynamic> data = jsonDecode(response.body);
            return data.cast<Map<String, dynamic>>();
          }
        } catch (e) {
          // Fall back to local if server fails
        }
      }

      // Get from local storage
      final prefs = await SharedPreferences.getInstance();
      final jsonData = prefs.getString(_chatHistoryKey);

      if (jsonData != null) {
        final List<dynamic> data = jsonDecode(jsonData);
        return data.cast<Map<String, dynamic>>();
      }

      return [];
    } catch (e) {
      return [];
    }
  }

  // Add a single message to history
  Future<bool> addMessageToHistory(Map<String, dynamic> message) async {
    final history = await getChatHistory();
    history.add(message);
    return saveChatHistory(history);
  }

  // Clear chat history (both local and server)
  Future<bool> clearChatHistory() async {
    try {
      // Clear local
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_chatHistoryKey);

      // Clear server
      final token = await _getAuthToken();
      if (token != null) {
        try {
          final response = await http
              .delete(
                Uri.parse('$_baseUrl/chats/history'),
                headers: {'Authorization': 'Bearer $token'},
              )
              .timeout(const Duration(seconds: 5));

          return response.statusCode == 200;
        } catch (e) {
          // Local clearance succeeded
          return true;
        }
      }

      return true;
    } catch (e) {
      return false;
    }
  }

  // SCHOOL MAP FUNCTIONS

  // Download and cache school map
  Future<String?> getCachedSchoolMap() async {
    try {
      // Check if we have a cached version
      final prefs = await SharedPreferences.getInstance();
      String? mapUrl = prefs.getString(_schoolMapCacheKey);

      if (mapUrl != null) {
        final File file = File(mapUrl);
        if (await file.exists()) {
          return mapUrl;
        }
      }

      // Download fresh copy
      final response = await http.get(
        Uri.parse('$_baseUrl/resources/school-map'),
      );

      if (response.statusCode == 200) {
        // Save to local file system
        final Directory appDir = await getApplicationDocumentsDirectory();
        final String filepath = '${appDir.path}/school_map.png';

        final File file = File(filepath);
        await file.writeAsBytes(response.bodyBytes);

        // Cache the path
        await prefs.setString(_schoolMapCacheKey, filepath);

        return filepath;
      }

      return null;
    } catch (e) {
      return null;
    }
  }

  // API Interaction with Ollama/LangChain

  // Send a message to the AI and get a response
  Future<Map<String, dynamic>> sendMessageToAI(String message) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': message}),
      );

      if (response.statusCode == 200) {
        return {'success': true, 'data': jsonDecode(response.body)};
      } else {
        return {'success': false, 'error': 'Failed to get AI response'};
      }
    } catch (e) {
      return {'success': false, 'error': 'Connection error: ${e.toString()}'};
    }
  }

  // Get available AI models
  Future<List<Map<String, dynamic>>> getAvailableModels() async {
    try {
      final response = await http.get(Uri.parse('$_baseUrl/models'));

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        return [];
      }
    } catch (e) {
      // Default models when server is unavailable
      return [
        {"id": "mistral", "name": "Mistral 7B"},
        {"id": "llama2", "name": "Llama 2 7B"},
      ];
    }
  }

  // Reset AI conversation
  Future<bool> resetAIConversation() async {
    try {
      final response = await http.post(Uri.parse('$_baseUrl/reset'));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // APP SETTINGS

  // Save app settings
  Future<void> saveAppSettings(Map<String, dynamic> settings) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonData = jsonEncode(settings);
    await prefs.setString(_appSettingsKey, jsonData);
  }

  // Get app settings with sensible defaults
  Future<Map<String, dynamic>> getAppSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonData = prefs.getString(_appSettingsKey);

    // Default settings
    final Map<String, dynamic> defaultSettings = {
      'serverUrl': _baseUrl,
      'language': 'en',
      'autoLogin': false,
      'theme': 'light',
      'fontSize': 'medium',
      'notifications': true,
      'aiModel': 'mistral',
    };

    if (jsonData != null) {
      final Map<String, dynamic> storedSettings = jsonDecode(jsonData);
      return {...defaultSettings, ...storedSettings};
    }

    return defaultSettings;
  }

  // Update a specific setting
  Future<void> updateSetting(String key, dynamic value) async {
    final settings = await getAppSettings();
    settings[key] = value;
    await saveAppSettings(settings);
  }

  // Get a specific setting with fallback value
  Future<T> getSetting<T>(String key, T defaultValue) async {
    final settings = await getAppSettings();
    return settings.containsKey(key) ? settings[key] as T : defaultValue;
  }
}
