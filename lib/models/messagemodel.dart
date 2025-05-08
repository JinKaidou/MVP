// lib/models/messagemodel.dart
class MessageModel {
  final String text;
  final bool isUser;
  final DateTime timestamp;

  MessageModel({
    required this.text,
    required this.isUser,
    required this.timestamp,
  });

  factory MessageModel.fromJson(Map<String, dynamic> json) {
    return MessageModel(
      text: json['text'] ?? '',
      isUser: json['is_user'] ?? false,
      timestamp:
          json['timestamp'] != null
              ? DateTime.parse(json['timestamp'])
              : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'text': text,
      'is_user': isUser,
      'timestamp': timestamp.toIso8601String(),
    };
  }
}
