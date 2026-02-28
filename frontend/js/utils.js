const AVATAR_COLORS = ["#6c63ff","#22c55e","#f59e0b","#ef4444","#3b82f6","#ec4899","#14b8a6"];

export function getInitial(name) {
  return name.charAt(0).toUpperCase();
}

export function avatarColor(name) {
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) & 0xffffffff;
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}
