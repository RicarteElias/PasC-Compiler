import sys
import copy

import lexer
from tag import Tag
from token1 import Token
from lexer import Lexer
from no import No


class AnalisadorParser:

    def __init__(self, lexer):
        self.lexer = lexer
        self.token = lexer.proxToken()  # Leitura inicial obrigatoria do primeiro simbolo
        if self.token is None:  # erro no Lexer
            sys.exit(0)

    def sinalizaErroSemantico(self, message):
        print("[Erro Semantico] na linha " + str(self.token.getLinha()) + " e coluna " + str(
            self.token.getColuna()) + ": ")
        print(message, "\n")

    def sinalizaErroSintatico(self, message):
        print("[Erro Sintatico] na linha " + str(self.token.getLinha()) + " e coluna " + str(
            self.token.getColuna()) + ": ")
        print(message, "\n")

    def advance(self):
        print("[DEBUG] token: ", self.token.toString())
        self.token = self.lexer.proxToken()
        if self.token is None:  # erro no Lexer
            sys.exit(0)

    def skip(self, message):
        self.sinalizaErroSintatico(message)
        self.advance()

    # verifica token esperado t
    def eat(self, t):
        if self.token.getNome() == t:
            self.advance()
            return True
        else:
            self.sinalizaErroSintatico("token esperado " + str(t))
            return False

    def prog(self):
        tokenTemp = copy.copy(self.token)
        self.eat(Tag.KW_PROGRAM)
        if self.eat(Tag.ID):
            lexer.TS.setType(tokenTemp, Tag.TIPO_VAZIO)
        self.body()

    def body(self):
        self.declList()
        self.eat(Tag.SMB_OBC)
        self.stmtList()
        self.eat(Tag.SMB_CBC)

    def declList(self):
        if self.token.getNome() == Tag.KW_NUM or self.token.getNome() == Tag.KW_CHAR:
            self.decl()
            self.eat(Tag.SMB_SEM)
            self.declList()

    def stmtList(self):
        pass

    def decl(self):
        self.idList(self.type())

    def type(self):
        no_type = No()
        if self.conferirToken([Tag.KW_NUM]):
            no_type.tipo = Tag.TIPO_NUMERO
            self.advance()
        elif self.conferirToken([Tag.KW_CHAR]):
            no_type.tipo = Tag.TIPO_LITERAL
            self.advance()
        else:
            self.sinalizaErroSintatico("Aguardando 'num' ou 'char'")
        return no_type

    def idList(self, tipo):
        tokenTemp = copy.copy(self.token)
        if self.eat(Tag.ID):
            lexer.TS.setType(tokenTemp.lexema, tipo)
        self.idListLinha()

    def idListLinha(self):
        if self.conferirToken([Tag.SMB_COM]):
            self.advance()
            self.idList(self.type())

    def stmtList(self):
        if self.token.getNome() == Tag.ID or self.token.getNome() == Tag.KW_IF or self.token.getNome() == Tag.KW_READ or self.token.getNome() == Tag.KW_WHILE or self.token.getNome() == Tag.KW_WRITE:
            self.stmt()
            self.eat(Tag.SMB_SEM)
            self.stmtList()

    def stmt(self):
        if self.token.getNome() == Tag.ID:
            self.assignStmt()
        elif self.token.getNome() == Tag.KW_IF:
            self.ifStmt()
        elif self.token.getNome() == Tag.KW_WHILE:
            self.whileStmt()
        elif self.token.getNome() == Tag.KW_READ:
            self.readStmt()
        elif self.token.getNome() == Tag.KW_WRITE:
            self.writeStmt()
        else:
            self.sinalizaErroSintatico("Comando inválido'")

    def writeStmt(self):
        self.eat(Tag.KW_WRITE)
        self.simpleExpr()

    def readStmt(self):
        self.eat(Tag.KW_READ)
        self.eat(Tag.ID)

    def whileStmt(self):
        self.stmtPrefix()
        self.eat(Tag.SMB_OBC)
        self.stmtList()
        self.eat(Tag.SMB_CBC)

    def ifStmt(self):
        self.eat(Tag.KW_IF)
        self.eat(Tag.SMB_OPA)
        self.expression()
        self.eat(Tag.SMB_CPA)
        self.eat(Tag.SMB_OBC)
        self.stmtList()
        self.eat(Tag.SMB_CBC)
        self.ifStmtLinha()

    def ifStmtLinha(self):
        if self.eat(Tag.KW_ELSE):
            self.eat(Tag.SMB_OBC)
            self.stmtList()
            self.eat(Tag.SMB_CBC)

    def assignStmt(self):

        if self.conferirToken([Tag.ID]):
            if lexer.TS.idIsNull(self.token.lexema):
                self.sinalizaErroSemantico("Identificador não foi declarado")
            self.advance()
        self.eat(Tag.OP_ATRIB)
        if self.simpleExpr() != lexer.TS.getType(self.token.lexema):
            self.sinalizaErroSemantico("Atribuição imcompativel")

    def stmtPrefix(self):
        self.eat(Tag.KW_WHILE)
        self.eat(Tag.SMB_OPA)
        self.expression()
        self.eat(Tag.SMB_CPA)

    def expression(self):
        self.simpleExpr()
        self.expressionLinha()

    def simpleExpr(self):
        noSimpE = No()
        noTerm = self.term()
        noSimpleExpr= self.simpleExprLinha()
        if noSimpleExpr.tipo == Tag.TIPO_VAZIO:
            noSimpE.tipo = noSimpleExpr.tipo

        return noSimpE



    def term(self):
        self.factorB()
        self.termLinha()

    def simpleExprLinha(self):
        noSeLi = No()
        if self.conferirToken([Tag.OP_EQ, Tag.OP_GT, Tag.OP_GE, Tag.OP_LT, Tag.OP_LE, Tag.OP_NE]):
            self.relop()
            self.term()
            self.simpleExprLinha()
        return noSeLi

    def factorB(self):
        self.factorA()
        self.factorBLinha()

    def termLinha(self):
        if self.conferirToken([Tag.OP_AD, Tag.OP_MIN]):
            self.addOP()
            self.factorB()
            self.termLinha()

    def expressionLinha(self):
        if self.conferirToken([Tag.KW_OR, Tag.KW_AND]):
            self.logop()
            self.simpleExpr()
            self.expressionLinha()

    def addOP(self):
        if self.conferirToken([Tag.OP_AD, Tag.OP_MIN]):
            self.advance()
        else:
            self.sinalizaErroSintatico("Operação inválida")

    def logop(self):
        if self.conferirToken([Tag.KW_OR, Tag.KW_AND]):
            self.advance()
        else:
            self.sinalizaErroSintatico("Esperado 'or' ou 'and'")

    def factor(self):
        factor = No()
        if self.conferirToken([Tag.ID]):

            self.advance()
        elif self.conferirToken([Tag.SMB_OPA]):
            self.eat(Tag.SMB_OPA)
            self.expression()
            self.eat(Tag.SMB_CPA)
        elif self.conferirToken([Tag.NUM_CONST, Tag.CHAR_CONST]):
            factor.tipo = self.constant()
        else:
            self.sinalizaErroSintatico("Fator inválido")

        return factor

    def factorA(self):
        if self.conferirToken([Tag.KW_NOT]):
            self.advance()
        self.factor()

    def constant(self):
        constant_t = No()
        if self.conferirToken([Tag.NUM_CONST]):
            constant_t.tipo = Tag.TIPO_NUMERO
            self.advance()
            return constant_t
        elif self.conferirToken([Tag.CHAR_CONST]):
            constant_t.tipo = Tag.TIPO_LITERAL
            self.advance()
            return constant_t
        else:
            self.sinalizaErroSintatico("Constante esperada'")

    def factorBLinha(self):
        if self.conferirToken([Tag.OP_DIV, Tag.OP_MUL]):
            self.mulop()
            self.factorA()
            self.factorBLinha()

    def mulop(self):
        if self.conferirToken([Tag.OP_MUL, Tag.OP_DIV]):
            self.advance()
        else:
            self.sinalizaErroSintatico("Operador inválido, utilize * ou /")

    def relop(self):
        if self.conferirToken([Tag.OP_EQ, Tag.OP_GT, Tag.OP_GE, Tag.OP_LT, Tag.OP_LE, Tag.OP_NE]):
            self.advance()
        else:
            self.sinalizaErroSintatico("Aguardando operador")

    def conferirToken(self, lista):
        return self.token.getNome() in lista
