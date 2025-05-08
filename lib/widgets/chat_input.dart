// lib/widgets/chat_input.dart
import 'package:flutter/material.dart';
import 'chat_button.dart';

class ChatInput extends StatefulWidget {
  final Function(String) onSend;
  final VoidCallback onMapRequested;
  final VoidCallback onAskToEdit;

  const ChatInput({
    super.key,
    required this.onSend,
    required this.onMapRequested,
    required this.onAskToEdit,
  });

  @override
  State<ChatInput> createState() => _ChatInputState();
}

class _ChatInputState extends State<ChatInput> {
  final TextEditingController _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Action buttons row
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              ActionButton(
                icon: Icons.map,
                onPressed: widget.onMapRequested,
                color: Colors.blue,
                tooltip: 'View Map',
              ),
              ActionButton(
                icon: Icons.edit_note,
                onPressed: widget.onAskToEdit,
                color: Colors.blue,
                tooltip: 'Ask to Edit',
              ),
              ActionButton(
                icon: Icons.smart_toy,
                onPressed: () {
                  widget.onSend("Tell me about the AI features");
                },
                color: Colors.blue,
                tooltip: 'AI Info',
              ),
            ],
          ),
        ),

        // Text input and send button
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 8.0),
          decoration: BoxDecoration(
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                spreadRadius: 1,
                blurRadius: 5,
                offset: const Offset(0, -1),
              ),
            ],
          ),
          child: Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(24.0),
                  ),
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      hintText: 'Type your message...',
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.symmetric(vertical: 12.0),
                    ),
                    maxLines: null,
                    textCapitalization: TextCapitalization.sentences,
                    onSubmitted: (text) {
                      if (text.trim().isNotEmpty) {
                        widget.onSend(text.trim());
                        _controller.clear();
                      }
                    },
                  ),
                ),
              ),
              const SizedBox(width: 8.0),
              Material(
                color: Colors.blue,
                borderRadius: BorderRadius.circular(24.0),
                child: InkWell(
                  onTap: () {
                    if (_controller.text.trim().isNotEmpty) {
                      widget.onSend(_controller.text.trim());
                      _controller.clear();
                    }
                  },
                  borderRadius: BorderRadius.circular(24.0),
                  child: Container(
                    padding: const EdgeInsets.all(12.0),
                    child: const Icon(
                      Icons.send_rounded,
                      color: Colors.white,
                      size: 20.0,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
