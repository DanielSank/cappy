name := "cappy"
version := "1.0"
scalaVersion := "2.11.7"

javacOptions ++= Seq("-source", "1.7", "-target", "1.7")

libraryDependencies ++= Seq(
  "io.netty" % "netty-all" % "4.1.0.Beta5" withSources(),
  "io.spray" %%  "spray-json" % "1.3.2"
)
