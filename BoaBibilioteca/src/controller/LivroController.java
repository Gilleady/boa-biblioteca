/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package controller;

import java.util.List;
import javax.swing.table.DefaultTableModel;
import model.Livro;
import model.LivroDAO;

/**
 *
 * @author gille
 */
public class LivroController {

    public List<Livro> listar(String pesquisa) {
        LivroDAO lDao = new LivroDAO();

        List<Livro> lista;
        if (pesquisa == null) {
            lista = lDao.listarLivros();
        } else {
            lista = lDao.pesquisarLivro(pesquisa);
        }
        return lista;
    }
}
