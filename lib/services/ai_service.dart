// lib/services/ai_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'dart:io' show Platform;

class AIService {
  // Dynamic base URL that works for different platforms
  String get baseUrl {
    if (kIsWeb) {
      return 'http://127.0.0.1:8000/api';
    } else if (Platform.isAndroid) {
      // For Android emulator or physical device testing
      const bool useLocalEmulator =
          false; // Changed to false to use physical device

      if (useLocalEmulator) {
        return 'http://10.0.2.2:8000/api'; // Android emulator
      } else {
        return 'http://192.168.0.129:8000/api'; // Your computer's IP address
      }
    } else {
      // iOS or other platforms
      return 'http://localhost:8000/api';
    }
  }

  Future<String> sendMessage(String message) async {
    print('Sending to: $baseUrl/chat');
    print('Message content: $message');

    // Handle empty messages
    if (message.trim().isEmpty) {
      return "Please enter a question about the USTP Student Handbook.";
    }

    // Maximum retries
    const maxRetries = 2;
    int retryCount = 0;

    while (retryCount <= maxRetries) {
      try {
        final response = await http
            .post(
              Uri.parse('$baseUrl/chat'),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({'message': message}),
            )
            .timeout(const Duration(
                seconds: 45)); // Longer timeout for LLM processing

        print('Response status: ${response.statusCode}');

        // Log truncated response for debugging
        final responsePreview = response.body.length > 100
            ? '${response.body.substring(0, 100)}...'
            : response.body;
        print('Response preview: $responsePreview');

        if (response.statusCode == 200) {
          final data = jsonDecode(response.body);
          return data['response'];
        } else if (response.statusCode == 202) {
          // Handle "still loading" status
          retryCount++;
          if (retryCount > maxRetries) {
            return "The server is still initializing. Please try again in a moment.";
          }
          // Wait before retrying
          await Future.delayed(Duration(seconds: 3));
          continue;
        } else {
          throw Exception('Failed to get response: ${response.statusCode}');
        }
      } catch (e) {
        print('Error occurred: $e');
        retryCount++;

        // If we've reached max retries, return error message
        if (retryCount > maxRetries) {
          if (e.toString().contains('timeout')) {
            return "The request timed out. The server might be processing a complex query or under heavy load.";
          }
          return "I'm having trouble connecting to the server. Please check your connection and try again.";
        }

        // Wait before retrying
        await Future.delayed(Duration(seconds: 2));
      }
    }

    // Fallback message if we somehow exit the loop
    return "Something went wrong. Please try again later.";
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
          .get(Uri.parse('$baseUrl/health'))
          .timeout(const Duration(seconds: 5));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
