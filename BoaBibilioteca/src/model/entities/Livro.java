package model.entities;

public class Livro {

    private String ISBN;
    private String titulo;
    private String autor;
    private String categoria;
    private String ano;
    private String editora;
    private int qtdCopias;

    public Livro() {
    }

    public Livro(String ISBN, String titulo, String autor, String categoria, String ano, String editora, int qtdCopias) {
        this.ISBN = ISBN;
        this.titulo = titulo;
        this.autor = autor;
        this.categoria = categoria;
        this.ano = ano;
        this.editora = editora;
        this.qtdCopias = qtdCopias;
    }

    public String getISBN() {
        return ISBN;
    }

    public void setISBN(String ISBN) {
        this.ISBN = ISBN;
    }

    public String getTitulo() {
        return titulo;
    }

    public void setTitulo(String titulo) {
        this.titulo = titulo;
    }

    public String getAutor() {
        return autor;
    }

    public void setAutor(String autor) {
        this.autor = autor;
    }

    public String getCategoria() {
        return categoria;
    }

    public void setCategoria(String categoria) {
        this.categoria = categoria;
    }

    public String getAno() {
        return ano;
    }

    public void setAno(String ano) {
        this.ano = ano;
    }

    public String getEditora() {
        return editora;
    }

    public void setEditora(String editora) {
        this.editora = editora;
    }
    
    public int getQtdCopias() {
        return qtdCopias;
    }

    public void setQtdCopias(int qtdCopias) {
        this.qtdCopias = qtdCopias;
    }
}
