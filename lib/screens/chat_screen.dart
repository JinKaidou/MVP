// lib/screens/chat_screen.dart
import 'package:flutter/material.dart';
import '../services/ai_service.dart';
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
  final TextEditingController _controller = TextEditingController();
  bool _isLoading = false;
  final List<String> _previousPrompts = [];
  final ScrollController _scrollController = ScrollController();
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  void initState() {
    super.initState();
    _addBotMessage(
      "Hi! User nice to see you again!\nHow can I be of assistance?",
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      backgroundColor: Colors.transparent,
      extendBodyBehindAppBar: true,
      drawer: _buildHistorySidebar(),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 4,
        shadowColor: Colors.black.withOpacity(0.16),
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(bottom: Radius.circular(20)),
        ),
        leading: IconButton(
          icon: const Icon(Icons.menu, color: Colors.black54),
          onPressed: () => _scaffoldKey.currentState?.openDrawer(),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.history, color: Colors.black54),
            onPressed: () => _scaffoldKey.currentState?.openDrawer(),
          ),
        ],
        title: const Text(''),
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              const Color(0xFFADD8E6).withOpacity(0.7), // Light blue at top
              Colors.white.withOpacity(0.7), // Almost white at bottom
            ],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: Column(
          children: [
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.only(
                  top: 100,
                  left: 16,
                  right: 16,
                  bottom: 16,
                ),
                itemCount: _messages.length,
                itemBuilder: (context, index) {
                  return _buildMessageRow(_messages[index]);
                },
              ),
            ),
            if (_isLoading)
              Container(
                padding: const EdgeInsets.all(8.0),
                alignment: Alignment.centerLeft,
                child: const Row(
                  children: [
                    SizedBox(width: 16),
                    SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    ),
                    SizedBox(width: 8),
                    Text(
                      "Typing...",
                      style: TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                  ],
                ),
              ),
            _buildInputArea(),
          ],
        ),
      ),
    );
  }

  Widget _buildHistorySidebar() {
    return Drawer(
      width: 260,
      backgroundColor: const Color(0xFFE5E5E5),
      child: Column(
        children: [
          SizedBox(
            height: 60,
            child: Align(
              alignment: Alignment.centerRight,
              child: IconButton(
                icon: const Icon(Icons.close, color: Colors.black87),
                onPressed: () => Navigator.pop(context),
              ),
            ),
          ),
          Expanded(
            child:
                _previousPrompts.isEmpty
                    ? const Center(
                      child: Text(
                        'No conversation history yet',
                        style: TextStyle(color: Colors.black54),
                      ),
                    )
                    : ListView.separated(
                      itemCount: _previousPrompts.length,
                      separatorBuilder:
                          (context, index) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final prompt = _previousPrompts[index];
                        return ListTile(
                          leading: const Icon(
                            Icons.chat_bubble_outline,
                            color: Colors.black54,
                          ),
                          title: Text(
                            prompt,
                            style: const TextStyle(
                              color: Colors.black87,
                              fontSize: 14,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          onTap: () {
                            _controller.text = prompt;
                            Navigator.pop(context);
                            // Move focus to text field
                            FocusScope.of(context).requestFocus(FocusNode());
                          },
                        );
                      },
                    ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageRow(Message message) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0),
      child: Row(
        mainAxisAlignment:
            message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!message.isUser) _buildBotAvatar(),
          const SizedBox(width: 8),
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color:
                    message.isUser
                        ? Colors.white
                        : const Color(
                          0xFFADD8E6,
                        ).withOpacity(0.86), // Light blue for bot
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.06),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Text(
                message.text,
                style: const TextStyle(color: Colors.black87, fontSize: 14),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBotAvatar() {
    return Container(
      width: 40,
      height: 40,
      margin: const EdgeInsets.only(right: 4),
      child: Image.asset('assets/icon/CGAI_logo.png', width: 40, height: 40),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(30),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.add_circle_outline, color: Colors.blue),
            onPressed: () {},
          ),
          Expanded(
            child: TextField(
              controller: _controller,
              decoration: const InputDecoration(
                hintText: 'Type a message...',
                border: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(horizontal: 8),
              ),
              maxLines: 1,
              textInputAction: TextInputAction.send,
              onSubmitted: _handleSubmit,
            ),
          ),
          IconButton(
            icon: const Icon(Icons.send, color: Colors.blue),
            onPressed: () => _handleSubmit(_controller.text),
          ),
        ],
      ),
    );
  }

  void _handleSubmit(String text) {
    if (text.trim().isEmpty) return;

    // Add user message
    setState(() {
      _messages.add(
        Message(text: text, isUser: true, timestamp: DateTime.now()),
      );
      _controller.clear();
      _isLoading = true;

      // Save to previous prompts if not already there
      if (!_previousPrompts.contains(text)) {
        _previousPrompts.insert(0, text);
        if (_previousPrompts.length > 5) {
          _previousPrompts.removeLast();
        }
      }
    });

    // Scroll to bottom
    _scrollToBottom();

    // Process message
    if (text.toLowerCase().contains('map')) {
      _processMapRequest();
    } else {
      _processRegularMessage(text);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _processMapRequest() {
    // Delay to simulate processing
    Future.delayed(const Duration(milliseconds: 500), () {
      setState(() {
        _isLoading = false;
      });

      // Show map screen with updated UI colors
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => const MapScreen(themeColor: Color(0xFFADD8E6)),
        ),
      );

      // Add bot response about map
      _addBotMessage("Here's the campus map!");
    });
  }

  void _processRegularMessage(String text) {
    // Example predefined response for enrollment
    if (text.toLowerCase().contains('enroll')) {
      Future.delayed(const Duration(milliseconds: 1000), () {
        setState(() {
          _isLoading = false;
        });
        _addBotMessage(
          "Kindly go to www.YourUni.com and fill up this enrollment form to enroll at YourUni",
        );
      });
      return;
    }

    // Otherwise, get response from AI service
    _aiService
        .sendMessage(text)
        .then((response) {
          setState(() {
            _isLoading = false;
          });
          _addBotMessage(response);
        })
        .catchError((error) {
          setState(() {
            _isLoading = false;
          });
          _addBotMessage("Sorry, I encountered an error: $error");
        });
  }

  void _addBotMessage(String text) {
    setState(() {
      _messages.add(
        Message(text: text, isUser: false, timestamp: DateTime.now()),
      );
    });
    _scrollToBottom();
  }
}
