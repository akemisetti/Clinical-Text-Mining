package com.votors.umls

import java.io.{FileWriter, PrintWriter}
import java.util.Date
import java.util.concurrent.atomic.AtomicInteger

import com.votors.common.Utils.Trace
import com.votors.common.{Conf, MyCache, Utils}
import com.votors.ml.{Ngram, Nlp, Sentence}
import org.apache.log4j.{Level, Logger}
import org.apache.spark.{SparkConf, SparkContext}

import scala.collection.mutable.ListBuffer
import scala.collection.JavaConversions.asScalaIterator
import scala.collection.immutable.{List, Range}
import scala.collection.mutable
import scala.collection.mutable.{ArrayBuffer, ListBuffer}
import scala.io.Source
import scala.io.Codec
/**
 * Created by Jason on 2016/4/1 0001.
 */
class TermIdentify {



}


/**
 *  input : a csv file, but only identify the text in one clumn.
 */
object TermIdentify {

  def main(avgs: Array[String]): Unit = {
    println("the input args are:\n" + avgs.mkString("\n"))
    if (avgs.size < 2) {
      println(s"invalid inputs, should be: prepare|parse dir file1,file2... extern-file")
      sys.exit(1)
    }
    val inFile = avgs(0)
    val outFile = avgs(1)
    // init spark
    val startTime = new Date()


    val records = Utils.readCsvFile(avgs(0)).toSeq
    val headSorted = Range(0,records.head.size()).map(index=>records.head.get(index)).zipWithIndex
    val head = headSorted.toMap
    var cnt = 0
    val tagger = new UmlsTagger2()

    var writer = new PrintWriter(new FileWriter(outFile))
    writer.println("INDEX,"+headSorted.map(_._1).mkString(",")+",CUI,AUI,CODE,STRING")

    records.tail.foreach(rec =>{
      cnt += 1
      if (true) {
        println(rec.toString)
        val hNgrams = mutable.LinkedHashMap[String,Ngram]()
        val sents = Nlp.generateSentence(cnt, rec.get(head("display_name")), null)
        val gramId = new AtomicInteger()
        Nlp.generateNgram(sents.toSeq, gramId, hNgrams)

        hNgrams.foreach(kv=>{
          val key = kv._1
          val gram = kv._2
          val (umlsBestScore, stys) = tagger.getUmlsScore(gram.text)
          if (umlsBestScore._3 != null && umlsBestScore._3.score>Conf.umlsLikehoodLimit) {
            val ret = tagger.execQuery(s"select code from umls.mrconso where CUI='${umlsBestScore._3.cui}' and AUI='${umlsBestScore._3.aui}';")
            var code = ""
            while (ret.next) {
              code += ret.getString("code") + ':'
            }
            println(s"${key},${umlsBestScore._3.cui},${code.dropRight(1)},${umlsBestScore._3.descr}")
            writer.println(s"${cnt},"+"\""+headSorted.map(keyIndex=>rec.get(keyIndex._2)).mkString("\",\"")+"\","+s"${umlsBestScore._3.cui},${umlsBestScore._3.aui},${code.dropRight(1)},${umlsBestScore._3.descr}")

          }
        })
      }
    })

    System.out.println("### used time: "+(new Date().getTime()-startTime.getTime())+" ###")
  }

}


/**
  *  input : a csv file, but only identify the text in one clumn.
  */
object TermIdentifySeq{

  def main(avgs: Array[String]): Unit = {
    println("the input args are:\n" + avgs.mkString("\n"))
    if (avgs.size < 2) {
      println(s"invalid inputs, should be: input_file  output-file")
      sys.exit(1)
    }
    val inFile = avgs(0)
    val outFile = avgs(1)
    // init spark
    val startTime = new Date()


    val records = Utils.readCsvFile(avgs(0)).toSeq
    val headSorted = Range(0,records.head.size()).map(index=>records.head.get(index)).zipWithIndex
    var cnt = 0
    val tagger = new UmlsTagger2()

    var writer = new PrintWriter(new FileWriter(outFile))
    writer.println("qaID\ttermID\tterm\tcui\taui\tscore\tcuiStr\tsentLen\tsentence")

    records.foreach(rec =>{
      cnt += 1
      if (true) {
//        println(rec.toString)
        val hNgrams = new ListBuffer[(Sentence,Ngram)]()
        val qaid = rec.get(0)
        print(s"${cnt}\t${qaid}\r")
        val sents = Nlp.generateSentence(cnt, rec.get(1), null)
        val gramId = new AtomicInteger()
        Nlp.generateNgramSeq(sents.toSeq, gramId, hNgrams)
        var termId = 0
        hNgrams.foreach(kv=>{
          val sent = kv._1
          val gram = kv._2
          val key = gram.key
//          println(key)
          val (umlsBestScore, stys) = tagger.getUmlsScore(gram.text)
          if (umlsBestScore != null && umlsBestScore._3 != null && umlsBestScore._3.score > Conf.umlsLikehoodLimit) {
            termId += 1
            val sugg = umlsBestScore._3
            val outStr = f"${qaid}\t${termId}\t${gram.textOrg}\t${sugg.cui}\t${sugg.aui}\t${sugg.score}%.0f\t${sugg.descr}\t${sent.sentId}\t${sent.words.mkString(" ")}"
            println(outStr)
            writer.println(outStr)
          }
        })
        if (cnt%100 == 0) writer.flush()
      }
    })
    writer.close()
    MyCache.close()
    System.out.println("### used time: "+(new Date().getTime()-startTime.getTime())+" ###")
  }

}