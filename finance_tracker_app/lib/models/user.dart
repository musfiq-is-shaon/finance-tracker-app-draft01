class User {
  final String id;
  final String email;
  final String? name;
  final DateTime createdAt;

  User({
    required this.id,
    required this.email,
    this.name,
    required this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'].toString(), // Convert int to String
      email: json['email'] as String,
      name: json['name'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'name': name,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

