import java.util.Random;

public class Main {
    public static void main(String[] args) {

        MyHashTable<MyTestingClass, String> table = new MyHashTable<>(100);
        Random random = new Random();

        for (int i = 0; i < 10000; i++) {
            int id = random.nextInt(1000);
            String name = "Student" + id;
            MyTestingClass student = new MyTestingClass(id, name);
            table.put(student, "Value " + i);
        }

        System.out.println("--- Hash Table Buckets ---");
        int[] bucketSizes = table.getBucketSizes();
        for (int i = 0; i < bucketSizes.length; i++) {
            System.out.println("Bucket " + i + ": " + bucketSizes[i] + " elements");
        }

        System.out.println("\n--- Binary Search Tree ---");
        BST<Integer, String> tree = new BST<>();
        tree.put(5, "Apple");
        tree.put(3, "Banana");
        tree.put(7, "Cherry");
        tree.put(1, "Date");
        tree.put(9, "Elderberry");

        System.out.println("Tree size: " + tree.size());

        for (BST.KVPair<Integer, String> elem : tree) {
            System.out.println("key is " + elem.getKey() + " and value is " + elem.getValue());
        }
    }
}