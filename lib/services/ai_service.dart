// lib/services/ai_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class AIService {
  // Change this to your computer's IP address when testing on a physical device
  // For emulator, use 10.0.2.2 (Android) or localhost (iOS)
  final String baseUrl = 'http://10.0.2.2:5000/api';

  Future<String> sendMessage(String message) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': message}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['response'];
      } else {
        throw Exception('Failed to get response: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error communicating with AI server: $e');
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
}
