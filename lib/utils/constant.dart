// lib/utils/constants.dart
import 'package:flutter/material.dart';

class AppColors {
  // Colors used in theme.dart
  static const primaryBlue = Color(0xFF2D7CFF);
  static const secondaryBlue = Color(0xFFE8F1FF);
  static const errorRed = Color(0xFFE53935);
  static const backgroundColor = Colors.white;
  static const backgroundcColor =
      Colors.white; // Note: there's a typo in your code
}

class AppTextStyles {
  // Text styles used in theme.dart
  static const TextStyle heading1 = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
  );

  static const TextStyle heading2 = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.bold,
  );

  static const TextStyle body = TextStyle(fontSize: 16);

  static const TextStyle bodyLight = TextStyle(
    fontSize: 16,
    color: Colors.grey,
  );

  static const TextStyle button = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.bold,
    color: Colors.white,
  );

  static const TextStyle caption = TextStyle(fontSize: 12, color: Colors.grey);
}

class AppConstants {
  // Constants used in theme.dart
  static const double inputBorderRadius = 24.0;
  static const double buttonBorderRadius = 8.0;
}
