// lib/widgets/action_button.dart
import 'package:flutter/material.dart';

class ActionButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onPressed;
  final Color color;
  final String? tooltip;

  const ActionButton({
    super.key,
    required this.icon,
    required this.onPressed,
    this.color = Colors.blue,
    this.tooltip,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip ?? '',
      child: Material(
        color: color,
        borderRadius: BorderRadius.circular(16.0),
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(16.0),
          child: Container(
            padding: const EdgeInsets.all(12.0),
            child: Icon(icon, color: Colors.white, size: 20.0),
          ),
        ),
      ),
    );
  }
}
