import java.util.Iterator;

public class BST<K extends Comparable<K>, V> implements Iterable<BST.KVPair<K, V>> {
    private Node root;
    private int size;

    private class Node {
        private K key;
        private V val;
        private Node left, right;

        public Node(K key, V val) {
            this.key = key;
            this.val = val;
        }
    }

    public static class KVPair<K, V> {
        private K key;
        private V val;

        public KVPair(K key, V val) {
            this.key = key;
            this.val = val;
        }

        public K getKey() {
            return key;
        }

        public V getValue() {
            return val;
        }
    }

    public void put(K key, V val) {
        root = put(root, key, val);
    }

    private Node put(Node x, K key, V val) {
        if (x == null) {
            size++;
            return new Node(key, val);
        }
        int cmp = key.compareTo(x.key);
        if (cmp < 0) {
            x.left = put(x.left, key, val);
        } else if (cmp > 0) {
            x.right = put(x.right, key, val);
        } else {
            x.val = val;
        }
        return x;
    }

    public V get(K key) {
        Node x = root;
        while (x != null) {
            int cmp = key.compareTo(x.key);
            if (cmp < 0) {
                x = x.left;
            } else if (cmp > 0) {
                x = x.right;
            } else {
                return x.val;
            }
        }
        return null;
    }

    public void delete(K key) {
        root = delete(root, key);
    }

    private Node delete(Node x, K key) {
        if (x == null) return null;
        int cmp = key.compareTo(x.key);
        if (cmp < 0) {
            x.left = delete(x.left, key);
        } else if (cmp > 0) {
            x.right = delete(x.right, key);
        } else {
            if (x.right == null) {
                size--;
                return x.left;
            }
            if (x.left == null) {
                size--;
                return x.right;
            }
            Node t = x;
            x = min(t.right);
            x.right = deleteMin(t.right);
            x.left = t.left;
        }
        return x;
    }

    private Node min(Node x) {
        if (x.left == null) return x;
        else return min(x.left);
    }

    private Node deleteMin(Node x) {
        if (x.left == null) {
            size--;
            return x.right;
        }
        x.left = deleteMin(x.left);
        return x;
    }

    public int size() {
        return size;
    }

    public Iterator<KVPair<K, V>> iterator() {
        return new Iterator<KVPair<K, V>>() {
            private Object[] array = new Object[size];
            private int count = 0;
            private int index = 0;

            {
                inOrder(root);
            }

            private void inOrder(Node node) {
                if (node == null) return;
                inOrder(node.left);
                array[count++] = new KVPair<>(node.key, node.val);
                inOrder(node.right);
            }

            public boolean hasNext() {
                return index < size;
            }

            public KVPair<K, V> next() {
                return (KVPair<K, V>) array[index++];
            }
        };
    }
}