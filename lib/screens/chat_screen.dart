// lib/screens/chat_screen.dart
import 'package:flutter/material.dart';
import '../services/ai_service.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/chat_input.dart';
import 'map_screen.dart';

class Message {
  final String text;
  final bool isUser;
  final DateTime timestamp;

  Message({required this.text, required this.isUser, required this.timestamp});
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final AIService _aiService = AIService();
  final List<Message> _messages = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _addBotMessage(
      "Hi there! I'm your campus guide AI. You can ask me anything about the campus, or tap the map button to view the campus map.",
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'CampusGuide AI',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.blue,
        elevation: 0,
      ),
      body: Column(
        children: [
          Expanded(
            child:
                _messages.isEmpty
                    ? const Center(
                      child: Text(
                        'Send a message to start chatting',
                        style: TextStyle(color: Colors.grey),
                      ),
                    )
                    : ListView.builder(
                      reverse: true,
                      itemCount: _messages.length,
                      itemBuilder: (context, index) {
                        final message = _messages[_messages.length - 1 - index];
                        return ChatBubble(
                          message: message.text,
                          isUser: message.isUser,
                          timestamp: message.timestamp,
                        );
                      },
                    ),
          ),
          // Loading indicator
          if (_isLoading)
            Container(
              padding: const EdgeInsets.all(8.0),
              alignment: Alignment.centerLeft,
              child: Row(
                children: [
                  const SizedBox(width: 16),
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    "Typing...",
                    style: TextStyle(color: Colors.grey[600], fontSize: 12),
                  ),
                ],
              ),
            ),
          // Chat input with action buttons
          ChatInput(
            onSend: _handleSendMessage,
            onMapRequested: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const MapScreen()),
              );
            },
            onAskToEdit: () {
              _handleSendMessage("Can you help me edit a document?");
            },
          ),
        ],
      ),
    );
  }

  void _addMessage(Message message) {
    setState(() {
      _messages.add(message);
    });
  }

  void _addBotMessage(String text) {
    _addMessage(Message(text: text, isUser: false, timestamp: DateTime.now()));
  }

  void _handleSendMessage(String text) async {
    // Add user message
    _addMessage(Message(text: text, isUser: true, timestamp: DateTime.now()));

    // Handle map-related queries directly to improve response time
    if (text.toLowerCase().contains('map') ||
        text.toLowerCase().contains('location') ||
        text.toLowerCase().contains('where')) {
      _addBotMessage(
        "I can show you the campus map. Would you like to see it?",
      );
      return;
    }

    // Set loading state
    setState(() {
      _isLoading = true;
    });

    try {
      // Get response from AI
      final response = await _aiService.sendMessage(text);

      // Remove loading state and add response
      setState(() {
        _isLoading = false;
        _addBotMessage(response);
      });
    } catch (e) {
      // Remove loading state and add error message
      setState(() {
        _isLoading = false;
        _addBotMessage("Sorry, I encountered an error. Please try again.");
      });
    }
  }
}
