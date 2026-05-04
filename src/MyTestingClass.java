public class MyTestingClass {
    private int id;
    private String name;

    public MyTestingClass(int id, String name) {
        this.id = id;
        this.name = name;
    }

    @Override
    public int hashCode() {
        int hash = 17;
        hash = 31 * hash + id;
        if (name != null) {
            for (int i = 0; i < name.length(); i++) {
                hash = 31 * hash + name.charAt(i);
            }
        }
        return hash;
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;
        MyTestingClass that = (MyTestingClass) obj;
        return id == that.id && name.equals(that.name);
    }
}