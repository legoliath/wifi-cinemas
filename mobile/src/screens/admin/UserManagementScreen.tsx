import React from 'react';
import { FlatList } from 'react-native';
import { Card, Avatar, Chip, useTheme } from 'react-native-paper';

const USERS = [
  { id: '1', name: 'Jean-Pierre Admin', email: 'admin@wificinemas.com', role: 'admin', active: true },
  { id: '2', name: 'Marie Directrice', email: 'director@prod.com', role: 'user', active: true },
  { id: '3', name: 'Sam Caméra', email: 'camera@prod.com', role: 'user', active: false },
];

export function UserManagementScreen() {
  const theme = useTheme();
  return (
    <FlatList data={USERS} style={{ flex: 1, backgroundColor: theme.colors.background }} contentContainerStyle={{ padding: 16, gap: 8 }}
      keyExtractor={(i) => i.id} renderItem={({ item }) => (
        <Card style={[{ elevation: 1 }, !item.active && { opacity: 0.5 }]}>
          <Card.Title title={item.name} subtitle={item.email}
            left={(p) => <Avatar.Text {...p} label={item.name.split(' ').map(n => n[0]).join('')} size={40} />}
            right={() => <Chip compact style={{ marginRight: 8 }} textStyle={{ fontSize: 11 }}>{item.role}</Chip>} />
        </Card>
    )} />
  );
}
