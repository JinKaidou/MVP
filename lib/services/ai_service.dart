// lib/services/ai_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'dart:io' show Platform;

class AIService {
  // Dynamic base URL that works for different platforms
  String get baseUrl {
    if (kIsWeb) {
      return 'http://127.0.0.1:5000/api'; // Using IP instead of localhost
    } else if (Platform.isAndroid) {
      // For Android emulator or physical device testing
      const bool useLocalEmulator = true; // Change to false for production

      if (useLocalEmulator) {
        return 'http://10.0.2.2:5000/api'; // Android emulator
      } else {
        return 'https://campus-guide-ai.onrender.com/api'; // Replace with your deployed server
      }
    } else {
      // iOS or other platforms
      return 'http://localhost:5000/api';
    }
  }

  Future<String> sendMessage(String message) async {
    print('Sending to: $baseUrl/chat');
    print('Message content: $message');

    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/chat'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'message': message}),
          )
          .timeout(const Duration(seconds: 30));

      print('Response status: ${response.statusCode}');
      print('Response body: ${response.body}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['response'];
      } else {
        throw Exception('Failed to get response: ${response.statusCode}');
      }
    } catch (e) {
      print('Error occurred: $e');
      return "I'm having trouble connecting to the server. Please check your connection and try again.";
    }
  }

  Future<void> resetConversation() async {
    try {
      await http.post(Uri.parse('$baseUrl/reset'));
    } catch (e) {
      throw Exception('Error resetting conversation: $e');
    }
  }

  Future<List<Map<String, dynamic>>> getAvailableModels() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/models'));

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to get models: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting available models: $e');
    }
  }

  // Health check to verify server connection
  Future<bool> isServerAvailable() async {
    try {
      final response = await http
          .get(
            Uri.parse('$baseUrl/health'),
          )
          .timeout(const Duration(seconds: 5));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
